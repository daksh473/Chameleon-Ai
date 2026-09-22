from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import Ticket, ConversationMessage, Customer
from ai.sentiment_classifier import classify_ticket, decide_action


def create_or_update_customer_for_support(
    db: Session,
    tenant_id: str,
    name: str,
    email: Optional[str] = None,
    channel: str = "dashboard",
    sentiment_score: float = 0.5,
) -> Customer:
    """
    Ensure customer exists for the given tenant and update conversation count and sentiment.
    Zero cross-tenant leakage: always queries with tenant_id.
    """
    customer = None
    if email:
        customer = db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            Customer.email == email
        ).first()
    
    if not customer:
        customer = db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            Customer.name == name
        ).first()

    if not customer:
        customer = Customer(
            tenant_id=tenant_id,
            name=name,
            email=email,
            source=channel,
            status="active",
            total_conversations=1,
            avg_sentiment=sentiment_score,
            total_tickets=0,
            last_contact=datetime.now(timezone.utc),
        )
        db.add(customer)
        db.flush()
    else:
        customer.total_conversations += 1
        # Exponential moving average for sentiment
        customer.avg_sentiment = round((customer.avg_sentiment * 0.7) + (sentiment_score * 0.3), 2)
        customer.last_contact = datetime.now(timezone.utc)
        if email and not customer.email:
            customer.email = email

    return customer


def create_support_ticket(
    db: Session,
    tenant_id: str,
    customer_name: str,
    issue: str,
    score: Optional[float] = None,
    channel: str = "dashboard",
    source: str = "dashboard",
    language: str = "en",
    customer_email: Optional[str] = None,
) -> Ticket:
    """
    Creates a new support ticket using the new PostgreSQL schema.
    If score is not provided, runs sentiment classifier to attach sentiment.
    Zero cross-tenant leakage: strictly isolated by tenant_id.
    """
    if score is None:
        try:
            sentiment_data = classify_ticket(issue)
            score = float(sentiment_data.get("score", 0.5))
            emotion = sentiment_data.get("emotion", "neutral")
            intent = sentiment_data.get("intent", "general_inquiry")
            urgency = sentiment_data.get("urgency_level", "LOW")
        except Exception:
            score = 0.5
            emotion = "neutral"
            intent = "general_inquiry"
            urgency = "LOW"
    else:
        emotion = "negative" if score < 0.3 else ("positive" if score > 0.7 else "neutral")
        intent = "support"
        urgency = "HIGH" if score < 0.3 else "LOW"

    # Priority mapped from sentiment
    if score < 0.3:
        priority = "HIGH"
    elif score <= 0.7:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    # Link/Create customer for this tenant
    customer = create_or_update_customer_for_support(
        db, tenant_id=tenant_id, name=customer_name, email=customer_email, channel=channel, sentiment_score=score
    )
    customer.total_tickets += 1

    # Get max ticket number for this tenant
    max_num = db.query(func.max(Ticket.ticket_number)).filter(Ticket.tenant_id == tenant_id).scalar() or 1000
    next_ticket_number = max_num + 1

    ticket = Ticket(
        tenant_id=tenant_id,
        ticket_number=next_ticket_number,
        customer_id=customer.id,
        customer_name=customer_name,
        issue=issue,
        status="OPEN",
        priority=priority,
        sentiment_score=score,
        emotion=emotion,
        intent=intent,
        urgency_level=urgency,
        channel=channel,
        source=source,
        language=language,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_tenant_tickets(
    db: Session,
    tenant_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Ticket]:
    """
    List tickets strictly for the authenticated tenant.
    Zero cross-tenant leakage.
    """
    query = db.query(Ticket).filter(Ticket.tenant_id == tenant_id)
    if status:
        query = query.filter(Ticket.status == status.upper())
    if priority:
        query = query.filter(Ticket.priority == priority.upper())
    return query.order_by(Ticket.created_at.desc()).offset(offset).limit(limit).all()


def get_tenant_ticket_by_id(db: Session, tenant_id: str, ticket_id: str) -> Optional[Ticket]:
    """
    Fetch a single ticket verifying tenant ownership.
    """
    return db.query(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        Ticket.id == ticket_id
    ).first()


def resolve_support_ticket(db: Session, tenant_id: str, ticket_id: str) -> Optional[Ticket]:
    """
    Mark a ticket as resolved for the tenant.
    """
    ticket = get_tenant_ticket_by_id(db, tenant_id, ticket_id)
    if not ticket:
        # Check by numeric ticket_number if string parsing matches
        try:
            t_num = int(ticket_id)
            ticket = db.query(Ticket).filter(
                Ticket.tenant_id == tenant_id,
                Ticket.ticket_number == t_num
            ).first()
        except ValueError:
            pass

    if ticket:
        ticket.status = "RESOLVED"
        ticket.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(ticket)
    return ticket


def get_support_stats(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Calculate support analytics for the authenticated tenant.
    """
    total = db.query(Ticket).filter(Ticket.tenant_id == tenant_id).count()
    open_count = db.query(Ticket).filter(Ticket.tenant_id == tenant_id, Ticket.status.in_(["OPEN", "IN_PROGRESS"])).count()
    resolved = db.query(Ticket).filter(Ticket.tenant_id == tenant_id, Ticket.status == "RESOLVED").count()
    escalated = db.query(Ticket).filter(Ticket.tenant_id == tenant_id, Ticket.status == "ESCALATED").count()
    critical = db.query(Ticket).filter(Ticket.tenant_id == tenant_id, Ticket.priority == "CRITICAL").count()

    avg_score = db.query(func.avg(Ticket.sentiment_score)).filter(Ticket.tenant_id == tenant_id).scalar() or 0.5

    return {
        "total": total,
        "open": open_count,
        "resolved": resolved,
        "escalated": escalated,
        "critical": critical,
        "average_sentiment": round(float(avg_score), 2),
    }


def save_support_conversation_message(
    db: Session,
    tenant_id: str,
    session_id: str,
    role: str,
    message: str,
    score: Optional[float] = None,
    emotion: Optional[str] = None,
    action: Optional[str] = None,
    channel: str = "dashboard",
    source: str = "ai_generated",
    sender_id: Optional[str] = None,
    sender_name: Optional[str] = None,
    ticket_id: Optional[str] = None,
) -> ConversationMessage:
    """
    Persist a message into the multi-tenant conversation_messages table.
    """
    msg = ConversationMessage(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        session_id=session_id,
        role=role,
        message=message,
        sentiment_score=score,
        emotion=emotion,
        action=action,
        channel=channel,
        source=source,
        sender_id=sender_id,
        sender_name=sender_name,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
