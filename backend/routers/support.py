from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.session import get_db
from core.tenancy import get_current_tenant_id
from services.support_service import (
    create_support_ticket,
    get_tenant_tickets,
    get_tenant_ticket_by_id,
    resolve_support_ticket,
    get_support_stats,
    save_support_conversation_message,
)
from ai.sentiment_classifier import classify_ticket, decide_action
from ai.bot_reply import generate_reply

router = APIRouter(prefix="/support", tags=["Support"])


# Pydantic Schemas
class TicketCreateRequest(BaseModel):
    customer_name: str
    issue: str
    sentiment_score: Optional[float] = None
    channel: Optional[str] = "dashboard"
    source: Optional[str] = "dashboard"
    language: Optional[str] = "en"
    customer_email: Optional[str] = None


class TicketResponseSchema(BaseModel):
    id: str
    tenant_id: str
    ticket_number: Optional[int] = None
    customer_name: str
    issue: str
    status: str
    priority: str
    sentiment_score: float
    emotion: str
    intent: Optional[str] = None
    urgency_level: str
    channel: str
    source: str
    created_at: str

    class Config:
        from_attributes = True


class IngestMessageRequest(BaseModel):
    channel: str = Field(..., description="e.g. telegram, email, webchat")
    sender_id: str = Field(..., description="Unique address or telegram handle")
    sender_name: str = Field(default="Customer")
    text: str
    session_id: Optional[str] = None


class SentimentAnalyzeRequest(BaseModel):
    message: str


# ── Endpoints ──

@router.post("/tickets")
def create_ticket_endpoint(
    req: TicketCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create a new support ticket attached to the authenticated tenant.
    Zero cross-tenant leakage.
    """
    ticket = create_support_ticket(
        db=db,
        tenant_id=tenant_id,
        customer_name=req.customer_name,
        issue=req.issue,
        score=req.sentiment_score,
        channel=req.channel,
        source=req.source,
        language=req.language,
        customer_email=req.customer_email,
    )
    return {
        "message": "Ticket created successfully",
        "ticket": {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "customer_name": ticket.customer_name,
            "issue": ticket.issue,
            "status": ticket.status,
            "priority": ticket.priority,
            "sentiment_score": ticket.sentiment_score,
            "emotion": ticket.emotion,
            "urgency_level": ticket.urgency_level,
            "channel": ticket.channel,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }
    }


@router.get("/tickets")
def list_tickets_endpoint(
    status: Optional[str] = Query(None, description="Filter by status: OPEN, IN_PROGRESS, RESOLVED, CLOSED"),
    priority: Optional[str] = Query(None, description="Filter by priority: CRITICAL, HIGH, MEDIUM, LOW"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    List support tickets strictly filtered by authenticated tenant.
    Zero cross-tenant leakage.
    """
    tickets = get_tenant_tickets(
        db=db,
        tenant_id=tenant_id,
        status=status,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "id": t.id,
            "ticket_number": t.ticket_number,
            "customer_name": t.customer_name,
            "customer_id": t.customer_id,
            "issue": t.issue,
            "status": t.status,
            "priority": t.priority,
            "sentiment_score": t.sentiment_score,
            "emotion": t.emotion,
            "intent": t.intent,
            "urgency_level": t.urgency_level,
            "channel": t.channel,
            "source": t.source,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
        }
        for t in tickets
    ]


@router.get("/tickets/{ticket_id}")
def get_ticket_endpoint(
    ticket_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get a single ticket ensuring it belongs to the authenticated tenant.
    """
    ticket = get_tenant_ticket_by_id(db=db, tenant_id=tenant_id, ticket_id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or access denied")
    return {
        "id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "customer_name": ticket.customer_name,
        "issue": ticket.issue,
        "status": ticket.status,
        "priority": ticket.priority,
        "sentiment_score": ticket.sentiment_score,
        "emotion": ticket.emotion,
        "urgency_level": ticket.urgency_level,
        "channel": ticket.channel,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
    }


@router.patch("/tickets/{ticket_id}/resolve")
def resolve_ticket_endpoint(
    ticket_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Mark a ticket as resolved for the authenticated tenant.
    """
    ticket = resolve_support_ticket(db=db, tenant_id=tenant_id, ticket_id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or access denied")
    return {
        "message": "Ticket resolved successfully",
        "ticket_id": ticket.id,
        "status": ticket.status,
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
    }


@router.get("/stats")
def support_stats_endpoint(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Retrieve real-time support queue statistics for the tenant.
    """
    return get_support_stats(db=db, tenant_id=tenant_id)


@router.post("/analyze")
def analyze_sentiment_endpoint(req: SentimentAnalyzeRequest):
    """
    Sentiment triage endpoint evaluating score, emotion, and recommended action.
    """
    classification = classify_ticket(req.message)
    score = classification.get("score", 0.5)
    emotion = classification.get("emotion", "neutral")
    action = decide_action(score)
    reply_data = generate_reply(req.message, action)

    return {
        "message": req.message,
        "score": score,
        "emotion": emotion,
        "action": action,
        "intent": classification.get("intent", "general_inquiry"),
        "urgency_level": classification.get("urgency_level", "LOW"),
        "reply": reply_data.get("answer"),
        "source": reply_data.get("source"),
    }


@router.post("/ingest")
def ingest_support_message(
    req: IngestMessageRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Ingest a message from Telegram, Email, or Webchat into the Support module.
    Automatically classifies sentiment, generates a reply or ticket, and saves history.
    """
    session_id = req.session_id or f"{req.channel}_{req.sender_id}"
    sentiment_data = classify_ticket(req.text)
    score = float(sentiment_data.get("score", 0.5))
    emotion = sentiment_data.get("emotion", "neutral")
    action = decide_action(score)

    ticket = None
    # If negative or urgent, automatically generate a ticket
    if action == "ESCALATE" or score < 0.35:
        ticket = create_support_ticket(
            db=db,
            tenant_id=tenant_id,
            customer_name=req.sender_name,
            issue=req.text,
            score=score,
            channel=req.channel,
            source=f"ingest-{req.channel}",
        )

    # Generate adaptive reply
    reply_data = generate_reply(req.text, action)
    reply_text = reply_data.get("answer", "")

    # Save to multi-tenant conversation messages
    save_support_conversation_message(
        db=db,
        tenant_id=tenant_id,
        session_id=session_id,
        role="user",
        message=req.text,
        score=score,
        emotion=emotion,
        action=action,
        channel=req.channel,
        source="inbound",
        sender_id=req.sender_id,
        sender_name=req.sender_name,
        ticket_id=ticket.id if ticket else None,
    )

    if reply_text:
        save_support_conversation_message(
            db=db,
            tenant_id=tenant_id,
            session_id=session_id,
            role="assistant",
            message=reply_text,
            score=score,
            emotion=emotion,
            action=action,
            channel=req.channel,
            source="ai_generated",
            ticket_id=ticket.id if ticket else None,
        )

    return {
        "status": "processed",
        "action": action,
        "sentiment": {"score": score, "emotion": emotion},
        "reply": reply_text,
        "ticket_created": ticket is not None,
        "ticket_id": ticket.id if ticket else None,
    }
