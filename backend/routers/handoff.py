from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import (
    get_agents, get_agent, create_agent, update_agent_status,
    create_handoff, get_handoffs, accept_handoff, resolve_handoff, transfer_handoff
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

@router.post("/auto-route")
def auto_route_api(req: AutoRouteRequest):
    return auto_route_agent(req.issue_text)
