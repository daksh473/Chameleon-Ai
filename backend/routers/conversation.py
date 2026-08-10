import uuid
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import save_conversation_message, get_conversation_history, create_ticket, create_voice_ticket
from ai.sentiment_classifier import analyze_sentiment, decide_action
from ai.bot_reply import generate_reply
from ai.language_ai import detect_language

from ai.memory_ai import (
    extract_customer_identifier, build_memory_context, extract_and_store_memories,
    generate_smart_greeting
)
from ai.customer_extractor import extract_customer_info
from database import upsert_customer_from_chat

router = APIRouter(prefix="/conversation", tags=["Conversation"])

class StartSessionResponse(BaseModel):
    session_id: str
    greeting: str = ""
    is_returning: bool = False

class MessageRequest(BaseModel):
    session_id: str
    message: str
    source: str = "text"
    audio_duration: float = 0

@router.post("/start", response_model=StartSessionResponse)
def start_session():
    session_id = str(uuid.uuid4())
    greeting_data = generate_smart_greeting(session_id)
    return {
        "session_id": session_id,
        "greeting": greeting_data["greeting"],
        "is_returning": greeting_data["is_returning"]
    }

@router.post("/message")
def send_message(req: MessageRequest):
    db_history = get_conversation_history(req.session_id)
    history_formatted = []
    for msg in db_history:
        history_formatted.append({"role": msg["role"], "content": msg["message"]})

    customer_id = extract_customer_identifier(req.message, req.session_id)
    memory_context, memory_count = build_memory_context(customer_id)

    detected_lang = detect_language(req.message)

    result = analyze_sentiment(req.message)
    action = decide_action(result["score"])
    reply_data = generate_reply(req.message, action, history_formatted, memory_context, detected_lang)
    reply = reply_data["answer"]
    reply_source = reply_data["source"]

    save_conversation_message(
        session_id=req.session_id, role="user", message=req.message,
        sentiment_score=result["score"], emotion=result["emotion"], action=action, language=detected_lang, channel=req.channel
    )
    save_conversation_message(
        session_id=req.session_id, role="assistant", message=reply,
        sentiment_score=result["score"], emotion=result["emotion"], action=action, language=detected_lang, channel=req.channel, source=reply_source
    )

    extract_and_store_memories(req.session_id, customer_id, req.message, reply, result["score"])

    crm_result = upsert_customer_from_chat(
        req.session_id,
        extract_customer_info(req.message),
        result["score"],
        req.message
    )
    ticket_name = crm_result.get("name") or f"Session {req.session_id[:8]}"

    ticket_created = False
    ticket_id = None
    if action == "ESCALATE":
        if req.source == "voice" and req.audio_duration > 0:
            ticket = create_voice_ticket(
                ticket_name, req.message,
                result["score"], result["emotion"], req.audio_duration
            )
        else:
            ticket = create_ticket(
                customer_name=ticket_name,
                issue=req.message,
                score=result["score"]
            )
        ticket_id = ticket["id"] if ticket else None
        ticket_created = True

        import asyncio
        async def trigger_handoff():
            async with httpx.AsyncClient() as client:
                try:
                    await client.post("http://127.0.0.1:8000/handoff/create", json={
                        "session_id": req.session_id,
                        "sentiment_score": result["score"],
                        "emotion": result["emotion"],
                        "conversation_history": [{"role": "user", "message": req.message}],
                        "customer_id": crm_result.get("customer_id") or 1
                    })
                except Exception as e:
                    print("Handoff trigger error:", e)
        asyncio.create_task(trigger_handoff())

    return {
        "score": result["score"],
        "emotion": result["emotion"],
        "reply": reply,
        "action": action,
        "language": detected_lang,
        "ticket_created": ticket_created,
        "ticket_id": ticket_id,
        "memory_used": memory_count,
        "customer_identifier": customer_id,
        "crm_customer_id": crm_result.get("customer_id"),
        "crm_customer_created": crm_result.get("created", False)
    }

@router.get("/{session_id}")
def get_session(session_id: str):
    history = get_conversation_history(session_id)
    return {"session_id": session_id, "messages": history}
