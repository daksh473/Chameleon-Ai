from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ai.sentiment_classifier import analyze_sentiment, decide_action
from ai.bot_reply import generate_reply
from ai.memory_ai import (
    extract_customer_identifier, build_memory_context, extract_and_store_memories,
    generate_smart_greeting, get_customer_profile_for_dashboard
)
from database import (
    init_db, save_conversation, get_all_conversations, save_conversation_message,
    create_ticket, create_voice_ticket, backfill_memories_from_db, store_memory
)
from dotenv import load_dotenv
import json
import asyncio
from ai.proactive_alerts import proactive_alert_cron

from routers import (
    support, billing, inventory, tasks, crm, analytics, tenants,
    tickets, conversation, knowledge, voice, email, handoff, memory, predict, language, excel, telegram
)
from db import Base, engine, SessionLocal
from core.tenancy import get_or_create_default_tenant
import httpx
import threading
from caspian_agent import start_caspian_listener

import os
from fastapi.staticfiles import StaticFiles

load_dotenv()
init_db()

app = FastAPI(title="Chameleon AI — Business Management System")

# Mount static files for generated PDF invoices and documents
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Initialize PostgreSQL Multi-tenant Schema & Seed Default Tenant
    try:
        from migrate_legacy_db import migrate_legacy_tables
        migrate_legacy_tables()
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            default_t = get_or_create_default_tenant(db)
            print(f"Multi-tenant PostgreSQL initialized. Default Tenant: {default_t.name} [{default_t.id}]")
    except Exception as e:
        print(f"PostgreSQL initialization error: {e}")

    # Start APScheduler background billing overdue scanner
    try:
        from services.billing_scheduler import start_billing_scheduler
        start_billing_scheduler()
    except Exception as e:
        print(f"Billing scheduler startup error: {e}")

    asyncio.create_task(proactive_alert_cron())
    try:
        result = backfill_memories_from_db()
        print(f"Memory backfill: {result}")
    except Exception as e:
        print(f"Memory backfill error: {e}")
        
    # Start the Caspian listener in a background thread
    thread = threading.Thread(target=start_caspian_listener, daemon=True)
    thread.start()
    print("Caspian listener thread started.")


@app.on_event("shutdown")
def shutdown_event():
    try:
        from services.billing_scheduler import stop_billing_scheduler
        stop_billing_scheduler()
    except Exception:
        pass


# ── 6 Core BMS Module Routers ──
app.include_router(support.router)      # /support
app.include_router(crm.router)          # /crm
app.include_router(billing.router)      # /billing
app.include_router(inventory.router)    # /inventory
app.include_router(tasks.router)        # /tasks
app.include_router(analytics.router)    # /analytics
app.include_router(tenants.router)      # /tenants

# ── Auxiliary & Legacy Compatibility Routers ──
app.include_router(tickets.router)
app.include_router(conversation.router)
app.include_router(knowledge.router)
app.include_router(voice.router)
app.include_router(email.router)
app.include_router(handoff.router)
app.include_router(memory.router)
app.include_router(predict.router)
app.include_router(language.router)
app.include_router(excel.router)
app.include_router(telegram.router)


class AgentConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

agent_manager = AgentConnectionManager()

class MessageRequest(BaseModel):
    message: str

@app.post("/analyze")
def analyze(req: MessageRequest):
    result = analyze_sentiment(req.message)
    action = decide_action(result["score"])
    reply_data = generate_reply(req.message, action)
    reply = reply_data["answer"]
    reply_source = reply_data["source"]
    save_conversation(req.message, result["score"], result["emotion"], action, reply)
    return {
        "message": req.message,
        "score":   result["score"],
        "emotion": result["emotion"],
        "action":  action,
        "reply":   reply,
        "source":  reply_source
    }

@app.get("/history")
def history():
    return get_all_conversations()

@app.websocket("/ws/agents")
async def agents_websocket_endpoint(websocket: WebSocket):
    await agent_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        agent_manager.disconnect(websocket)

def parse_ws_message(raw: str) -> dict:
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("text"):
            return data
    except json.JSONDecodeError:
        pass
    return {"text": raw, "source": "text", "audio_duration": 0, "language": "en"}

async def process_message(data: str, session_id: str, customer_id: str, chat_history: list, crm_customer_id: int = None) -> tuple:
    parsed = parse_ws_message(data)
    text = parsed.get("text", "").strip()
    source = parsed.get("source", "text")
    audio_duration = float(parsed.get("audio_duration", 0))
    language = parsed.get("language", "en")

    customer_id = extract_customer_identifier(text, session_id, customer_id)
    memory_context, memory_count = build_memory_context(customer_id)

    history_formatted = []
    for msg in chat_history[-10:]:
        role = msg.get("role", "user")
        content = msg.get("message") or msg.get("content", "")
        history_formatted.append({"role": role, "content": content})

    from ai.language_ai import detect_language
    detected_lang = detect_language(text)

    result = analyze_sentiment(text)
    action = decide_action(result["score"])
    reply_data = generate_reply(text, action, history_formatted, memory_context, detected_lang)
    reply = reply_data["answer"]
    reply_source = reply_data["source"]

    save_conversation_message(session_id, "user", text, result["score"], result["emotion"], action, detected_lang)
    save_conversation_message(session_id, "assistant", reply, result["score"], result["emotion"], action, detected_lang, source=reply_source)
    save_conversation(text, result["score"], result["emotion"], action, reply)

    chat_history.append({"role": "user", "message": text, "sentiment": result["score"], "language": detected_lang})
    chat_history.append({"role": "assistant", "message": reply, "language": detected_lang})

    crm_result = None
    try:
        async with httpx.AsyncClient() as client:
            crm_res = await client.post("http://127.0.0.1:8000/crm/customers/from-chat", json={
                "session_id": session_id,
                "message": text,
                "sentiment_score": result["score"]
            })
            if crm_res.status_code == 200:
                crm_result = crm_res.json()
                crm_customer_id = crm_result.get("customer_id") or crm_customer_id
    except Exception as e:
        print(f"CRM sync error: {e}")

    ticket_name = (crm_result or {}).get("name") or f"Session {customer_id[:12]}"

    ticket_id = None
    if action == "ESCALATE":
        if source == "voice" and audio_duration > 0:
            ticket = create_voice_ticket(
                ticket_name, text, result["score"], result["emotion"], audio_duration, detected_lang
            )
        else:
            ticket = create_ticket(
                customer_name=ticket_name,
                issue=text,
                score=result["score"],
                language=detected_lang
            )
        ticket_id = ticket["id"] if ticket else None

        try:
            from handoff_service import trigger_handoff
            hid = trigger_handoff(
                customer_message=text,
                sentiment_score=result["score"],
                emotion=result["emotion"],
                channel="live_chat",
                session_id=session_id,
                conversation_history=chat_history,
                customer_id=crm_customer_id or 1
            )
            print(f"Handoff {hid} created for live chat")
        except Exception as e:
            print(f"Handoff error: {e}")

    extract_and_store_memories(session_id, customer_id, text, reply, result["score"])

    if source == "voice" and language:
        store_memory(session_id, customer_id, "preference", "language", language, 0.6)

    response = {
        "type": "message",
        "message": text,
        "score": result["score"],
        "emotion": result["emotion"],
        "action": action,
        "reply": reply,
        "language": detected_lang,
        "memory_used": memory_count,
        "customer_identifier": customer_id,
        "source": source,
        "ticket_id": ticket_id,
        "crm_customer_id": crm_customer_id,
        "crm_customer_created": crm_result.get("created") if crm_result else False,
    }
    return response, customer_id, crm_customer_id

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected!")
    session_id = "live_" + str(id(websocket))
    customer_id = session_id
    crm_customer_id = None
    chat_history = []

    # Send greeting — wrapped in try/except so a failed AI call doesn't kill the connection
    try:
        greeting_data = generate_smart_greeting(customer_id)
        profile = get_customer_profile_for_dashboard(customer_id)
        await websocket.send_text(json.dumps({
            "type": "greeting",
            "message": greeting_data["greeting"],
            "is_returning": greeting_data["is_returning"],
            "memory_count": greeting_data["memory_count"],
            "profile": profile
        }))
    except Exception as e:
        print(f"Greeting generation failed: {e}")
        await websocket.send_text(json.dumps({
            "type": "greeting",
            "message": "Welcome to Sentiment AI! How can I help you today?",
            "is_returning": False,
            "memory_count": 0,
            "profile": {}
        }))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                response, customer_id, crm_customer_id = await process_message(
                    raw, session_id, customer_id, chat_history, crm_customer_id
                )
                await websocket.send_text(json.dumps(response))
            except Exception as msg_err:
                print(f"Message processing error: {msg_err}")
                await websocket.send_text(json.dumps({
                    "type": "message",
                    "message": raw,
                    "score": 0.5,
                    "emotion": "neutral",
                    "action": "NORMAL",
                    "reply": "I'm having trouble processing your request right now. Please try again.",
                    "language": "en",
                    "memory_used": 0,
                    "source": "text"
                }))
    except Exception as e:
        print(f"Client disconnected: {e}")
