from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from db.session import get_db
from core.tenancy import get_current_tenant_id
from services.support_service import (
    create_support_ticket,
    get_tenant_tickets,
    get_tenant_ticket_by_id,
    resolve_support_ticket,
    get_support_stats,
)

router = APIRouter(prefix="/tickets", tags=["Tickets (Legacy Alias)"])


class TicketCreateRequest(BaseModel):
    customer_name: str
    issue: str
    sentiment_score: float
    channel: Optional[str] = "dashboard"


@router.post("/create")
def create_new_ticket(
    req: TicketCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    ticket = create_support_ticket(
        db=db,
        tenant_id=tenant_id,
        customer_name=req.customer_name,
        issue=req.issue,
        score=req.sentiment_score,
        channel=req.channel or "dashboard",
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
            "channel": ticket.channel,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }
    }


@router.get("")
def list_tickets(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    tickets = get_tenant_tickets(db=db, tenant_id=tenant_id)
    return [
        {
            "id": t.id,
            "ticket_number": t.ticket_number,
            "customer_name": t.customer_name,
            "customer_id": t.customer_id,
            "issue": t.issue,
            "status": t.status,
            "priority": t.priority,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
            "language": t.language,
            "source": t.source,
        }
        for t in tickets
    ]


@router.patch("/{ticket_id}/resolve")
def resolve_existing_ticket(
    ticket_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    ticket = resolve_support_ticket(db=db, tenant_id=tenant_id, ticket_id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {
        "message": "Ticket resolved",
        "ticket": {
            "id": ticket.id,
            "status": ticket.status,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        }
    }


@router.get("/stats")
def tickets_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    return get_support_stats(db=db, tenant_id=tenant_id)
