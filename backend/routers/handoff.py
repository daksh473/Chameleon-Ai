from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import (
    get_agents, get_agent, create_agent, update_agent_status,
    create_handoff, get_handoffs, get_handoff, accept_handoff, resolve_handoff, transfer_handoff
)
from ai.crm_ai import auto_route_agent

router = APIRouter(prefix="/handoff", tags=["Handoff"])

class AgentCreate(BaseModel):
    name: str
    email: str
    specialization: str = "general"
    max_conversations: int = 3

class AgentStatusUpdate(BaseModel):
    status: str

class HandoffCreate(BaseModel):
    session_id: str
    customer_id: Optional[int] = None
    sentiment_score: Optional[float] = None
    emotion: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = []

class HandoffResolve(BaseModel):
    resolution_notes: str
    customer_rating: Optional[int] = None

class HandoffTransfer(BaseModel):
    new_agent_id: int
    reason: str

class AutoRouteRequest(BaseModel):
    issue_text: str

@router.get("/agents")
def list_agents():
    return get_agents()

@router.post("/agents")
def add_agent(req: AgentCreate):
    aid = create_agent(req.name, req.email, req.specialization, req.max_conversations)
    return {"id": aid}

@router.put("/agents/{agent_id}/status")
def change_agent_status(agent_id: int, req: AgentStatusUpdate):
    if req.status not in ["online", "busy", "offline"]:
        raise HTTPException(400, "Invalid status")
    agent = update_agent_status(agent_id, req.status)
    return {"success": True, "agent": agent}

from handoff_service import trigger_handoff

@router.post("/create")
def new_handoff(req: HandoffCreate):
    issue_preview = "General inquiry"
    if req.conversation_history:
        issue_preview = req.conversation_history[-1].get("message", "")[:200]
        
    hid = trigger_handoff(
        customer_message=issue_preview,
        sentiment_score=req.sentiment_score,
        emotion=req.emotion,
        channel="live_chat",
        session_id=req.session_id,
        conversation_history=req.conversation_history,
        customer_id=req.customer_id
    )

    return {
        "handoff_id": hid,
        "success": True
    }

@router.post("/accept/{handoff_id}")
def accept_handoff_api(handoff_id: int):
    accept_handoff(handoff_id)
    return {"success": True}

@router.post("/resolve/{handoff_id}")
def resolve_handoff_api(handoff_id: int, req: HandoffResolve):
    resolve_handoff(handoff_id, req.resolution_notes, req.customer_rating)
    return {"success": True}

@router.post("/transfer/{handoff_id}")
def transfer_handoff_api(handoff_id: int, req: HandoffTransfer):
    transfer_handoff(handoff_id, req.new_agent_id, req.reason)
    return {"success": True}

@router.get("/queue")
def queue():
    return get_handoffs(status="pending")

@router.get("/active")
def active():
    return get_handoffs(status="active")

@router.get("/agent/{agent_id}")
def agent_handoffs(agent_id: int):
    return get_handoffs(agent_id=agent_id)

class AgentMessageRequest(BaseModel):
    message: str

class AddPhoneRequest(BaseModel):
    phone: str

@router.post("/agent-message/{handoff_id}")
def agent_message(handoff_id: str, body: AgentMessageRequest):
    from messaging_service import send_agent_message
    
    result = send_agent_message(int(handoff_id), body.message)
    
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result)
        
    return result

@router.post("/call-customer/{handoff_id}")
def call_customer(handoff_id: int):
    handoff = get_handoff(handoff_id)
    if not handoff:
        raise HTTPException(404, "Handoff not found")
        
    customer_id = handoff.get("customer_id")
    if not customer_id:
        raise HTTPException(400, {"error": "no_phone_number", "message": "No customer linked to this handoff."})
        
    import sqlite3
    from database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
    finally:
        conn.close()
        
    if not row or not row["phone"]:
        raise HTTPException(400, {"error": "no_phone_number", "message": "No phone number on file for this customer."})
        
    phone = row["phone"]
    
    # Twilio Call
    import os
    from twilio.rest import Client
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not account_sid or not auth_token:
        # Mock call if twilio not configured for testing
        print(f"MOCK CALL to {phone} (Twilio not configured)")
        from database import log_call
        call_id = log_call(handoff_id, customer_id, handoff["agent_id"], "mock_sid_12345", "completed")
        return {"success": True, "call_id": call_id, "status": "mock_completed", "message": "Twilio not configured, mock call logged."}

    client = Client(account_sid, auth_token)
    try:
        call = client.calls.create(
            twiml='<Response><Say>Please hold while we connect you to an agent.</Say></Response>',
            to=phone,
            from_=twilio_number
        )
        
        from database import log_call
        call_id = log_call(handoff_id, customer_id, handoff["agent_id"], call.sid, call.status)
        return {"success": True, "call_id": call_id, "status": call.status, "sid": call.sid}
    except Exception as e:
        raise HTTPException(500, f"Twilio call failed: {e}")

@router.post("/add-phone/{handoff_id}")
def add_phone(handoff_id: int, req: AddPhoneRequest):
    handoff = get_handoff(handoff_id)
    if not handoff or not handoff.get("customer_id"):
        raise HTTPException(404, "Customer not found")
        
    from database import update_customer_phone
    update_customer_phone(handoff["customer_id"], req.phone)
    return {"success": True, "phone": req.phone}

@router.post("/auto-route")
def auto_route_api(req: AutoRouteRequest):
    return auto_route_agent(req.issue_text)
