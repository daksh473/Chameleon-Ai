from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from db.models import Customer, Lead, LeadActivity, Ticket


# ==============================================================================
# CUSTOMER CRUD & OPERATIONS
# ==============================================================================

def create_customer(
    db: Session,
    tenant_id: str,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    source: str = "direct",
    notes: Optional[str] = None,
    tags: Optional[str] = None,
) -> Customer:
    """
    Create a new customer strictly associated with tenant_id.
    Zero cross-tenant leakage.
    """
    customer = Customer(
        tenant_id=tenant_id,
        name=name,
        email=email,
        phone=phone,
        company=company,
        source=source,
        notes=notes,
        tags=tags,
        status="active",
        risk_score=0.5,
        total_conversations=0,
        avg_sentiment=0.5,
        total_tickets=0,
        revenue_generated=0.00,
        last_contact=datetime.now(timezone.utc),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    # Log creation activity
    log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="note",
        description=f"Customer '{name}' created in CRM.",
        customer_id=customer.id,
    )

    return customer


def get_customers(
    db: Session,
    tenant_id: str,
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Customer]:
    """
    List customers for the tenant with optional search query.
    """
    query = db.query(Customer).filter(Customer.tenant_id == tenant_id)
    if status:
        query = query.filter(Customer.status == status)
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(s),
                Customer.email.ilike(s),
                Customer.company.ilike(s),
                Customer.phone.ilike(s),
            )
        )
    return query.order_by(Customer.created_at.desc()).offset(offset).limit(limit).all()


def get_customer_by_id(db: Session, tenant_id: str, customer_id: str) -> Optional[Customer]:
    """
    Fetch a single customer verifying tenant isolation.
    """
    return db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.id == customer_id,
    ).first()


def update_customer(
    db: Session,
    tenant_id: str,
    customer_id: str,
    data: Dict[str, Any],
) -> Optional[Customer]:
    """
    Update customer details verifying tenant isolation.
    """
    customer = get_customer_by_id(db, tenant_id, customer_id)
    if not customer:
        return None

    allowed_fields = [
        "name", "email", "phone", "company", "source",
        "status", "risk_score", "notes", "tags", "revenue_generated"
    ]
    for key, val in data.items():
        if key in allowed_fields and val is not None:
            setattr(customer, key, val)

    customer.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, tenant_id: str, customer_id: str) -> bool:
    """
    Delete a customer verifying tenant isolation.
    """
    customer = get_customer_by_id(db, tenant_id, customer_id)
    if not customer:
        return False
    db.delete(customer)
    db.commit()
    return True


def get_customer_profile(db: Session, tenant_id: str, customer_id: str) -> Optional[Dict[str, Any]]:
    """
    Return comprehensive customer profile: details, timeline, deals/leads, tickets.
    """
    customer = get_customer_by_id(db, tenant_id, customer_id)
    if not customer:
        return None

    # Fetch activities
    activities = db.query(LeadActivity).filter(
        LeadActivity.tenant_id == tenant_id,
        LeadActivity.customer_id == customer_id,
    ).order_by(LeadActivity.created_at.desc()).limit(30).all()

    # Fetch linked leads/deals
    leads = db.query(Lead).filter(
        Lead.tenant_id == tenant_id,
        Lead.customer_id == customer_id,
    ).order_by(Lead.created_at.desc()).all()

    # Fetch support tickets
    tickets = db.query(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        Ticket.customer_id == customer_id,
    ).order_by(Ticket.created_at.desc()).all()

    return {
        "profile": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "company": customer.company,
            "source": customer.source,
            "status": customer.status,
            "risk_score": customer.risk_score,
            "total_conversations": customer.total_conversations,
            "avg_sentiment": customer.avg_sentiment,
            "total_tickets": customer.total_tickets,
            "revenue_generated": float(customer.revenue_generated),
            "notes": customer.notes,
            "tags": customer.tags,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
        },
        "timeline": [
            {
                "id": a.id,
                "type": a.activity_type,
                "description": a.description,
                "sentiment_score": a.sentiment_score,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in activities
        ],
        "leads": [
            {
                "id": l.id,
                "title": l.title or l.name,
                "value": float(l.estimated_value),
                "stage": l.status,
                "probability": l.probability,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in leads
        ],
        "tickets": [
            {
                "id": t.id,
                "ticket_number": t.ticket_number,
                "issue": t.issue,
                "status": t.status,
                "priority": t.priority,
                "sentiment_score": t.sentiment_score,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tickets
        ],
        "total_interactions": customer.total_conversations + len(activities) + len(tickets),
    }


# ==============================================================================
# LEAD CRUD & STATUS PIPELINE
# ==============================================================================

VALID_LEAD_STAGES = ["new", "contacted", "qualified", "proposal", "won", "lost"]
STAGE_ALIASES = {
    "lead": "new",
    "negotiation": "proposal",
}

def normalize_stage(stage: str) -> str:
    s = stage.lower().strip()
    return STAGE_ALIASES.get(s, s)


def create_lead(
    db: Session,
    tenant_id: str,
    name: str,
    title: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    status: str = "new",
    estimated_value: float = 0.00,
    probability: int = 20,
    source: str = "web",
    customer_id: Optional[str] = None,
    notes: Optional[str] = None,
    assigned_to_user_id: Optional[str] = None,
) -> Lead:
    """
    Create a new sales lead / opportunity in the pipeline.
    Zero cross-tenant leakage.
    """
    normalized_status = normalize_stage(status)
    if normalized_status not in VALID_LEAD_STAGES:
        normalized_status = "new"

    lead = Lead(
        tenant_id=tenant_id,
        name=name,
        title=title or f"Opportunity with {name}",
        email=email,
        phone=phone,
        company=company,
        status=normalized_status,
        estimated_value=estimated_value,
        probability=probability,
        source=source,
        customer_id=customer_id,
        notes=notes,
        assigned_to_user_id=assigned_to_user_id,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # Log activity
    log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="note",
        description=f"Lead created: {lead.title} (${estimated_value:,.2f})",
        lead_id=lead.id,
        customer_id=customer_id,
    )

    return lead


def get_leads(
    db: Session,
    tenant_id: str,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Lead]:
    """
    List leads strictly for the authenticated tenant.
    """
    query = db.query(Lead).filter(Lead.tenant_id == tenant_id)
    if status:
        query = query.filter(Lead.status == normalize_stage(status))
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Lead.name.ilike(s),
                Lead.title.ilike(s),
                Lead.company.ilike(s),
                Lead.email.ilike(s),
            )
        )
    return query.order_by(Lead.created_at.desc()).offset(offset).limit(limit).all()


def get_lead_by_id(db: Session, tenant_id: str, lead_id: str) -> Optional[Lead]:
    """
    Fetch a single lead verifying tenant isolation.
    """
    return db.query(Lead).filter(
        Lead.tenant_id == tenant_id,
        Lead.id == lead_id,
    ).first()


def update_lead(
    db: Session,
    tenant_id: str,
    lead_id: str,
    data: Dict[str, Any],
) -> Optional[Lead]:
    """
    Update lead details or stage in the kanban pipeline.
    """
    lead = get_lead_by_id(db, tenant_id, lead_id)
    if not lead:
        return None

    old_status = lead.status
    allowed = ["name", "title", "email", "phone", "company", "status", "estimated_value", "probability", "source", "notes", "customer_id", "assigned_to_user_id"]
    for key, val in data.items():
        if key in allowed and val is not None:
            if key == "status":
                val = normalize_stage(str(val))
            setattr(lead, key, val)

    lead.updated_at = datetime.now(timezone.utc)

    # If stage changed, log pipeline movement
    if old_status != lead.status:
        log_activity(
            db=db,
            tenant_id=tenant_id,
            activity_type="status_change",
            description=f"Lead moved from '{old_status.upper()}' to '{lead.status.upper()}'.",
            lead_id=lead.id,
            customer_id=lead.customer_id,
        )

    db.commit()
    db.refresh(lead)
    return lead


def delete_lead(db: Session, tenant_id: str, lead_id: str) -> bool:
    """
    Delete a lead verifying tenant isolation.
    """
    lead = get_lead_by_id(db, tenant_id, lead_id)
    if not lead:
        return False
    db.delete(lead)
    db.commit()
    return True


def convert_lead_to_customer(
    db: Session,
    tenant_id: str,
    lead_id: str,
) -> Optional[Customer]:
    """
    Converts a sales lead into an active paying customer:
    1. Updates or creates Customer record
    2. Links lead to the customer
    3. Marks lead status as 'won'
    4. Logs activity in the timeline
    """
    lead = get_lead_by_id(db, tenant_id, lead_id)
    if not lead:
        return None

    # Check if customer already exists for this lead
    customer = None
    if lead.customer_id:
        customer = get_customer_by_id(db, tenant_id, lead.customer_id)

    if not customer and lead.email:
        customer = db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            Customer.email == lead.email,
        ).first()

    if not customer:
        customer = Customer(
            tenant_id=tenant_id,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            source=lead.source or "lead_conversion",
            status="active",
            revenue_generated=lead.estimated_value,
            last_contact=datetime.now(timezone.utc),
        )
        db.add(customer)
        db.flush()
    else:
        customer.revenue_generated = float(customer.revenue_generated) + float(lead.estimated_value)
        customer.status = "active"

    # Link and mark lead as won
    lead.customer_id = customer.id
    lead.status = "won"
    lead.probability = 100
    lead.updated_at = datetime.now(timezone.utc)

    # Log conversion in timeline
    log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="deal",
        description=f"Lead converted to Customer! Deal won: {lead.title} (${float(lead.estimated_value):,.2f})",
        lead_id=lead.id,
        customer_id=customer.id,
    )

    db.commit()
    db.refresh(customer)
    return customer


# ==============================================================================
# PIPELINE KANBAN & TIMELINE
# ==============================================================================

def get_crm_pipeline(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Returns grouped pipeline kanban columns by stage with values and lead cards.
    Supports standard kanban stages.
    """
    leads = db.query(Lead).filter(Lead.tenant_id == tenant_id).order_by(Lead.created_at.desc()).all()

    pipeline_stages = ["new", "contacted", "qualified", "proposal", "won", "lost"]
    res = {
        stage: {
            "stage": stage,
            "total_value": 0.0,
            "count": 0,
            "deals": [],  # Named deals for frontend Kanban compatibility
            "leads": [],
        }
        for stage in pipeline_stages
    }

    # Also provide alias mappings for frontend compatibility ("lead" -> "new", "negotiation" -> "proposal")
    res["lead"] = res["new"]
    res["negotiation"] = res["proposal"]

    for l in leads:
        stage = l.status if l.status in res else "new"
        lead_card = {
            "id": l.id,
            "title": l.title or l.name,
            "customer_name": l.name,
            "company": l.company,
            "value": float(l.estimated_value),
            "probability": l.probability,
            "stage": stage,
            "source": l.source,
            "expected_close": l.created_at.isoformat() if l.created_at else None,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        res[stage]["leads"].append(lead_card)
        res[stage]["deals"].append(lead_card)
        res[stage]["total_value"] += float(l.estimated_value)
        res[stage]["count"] += 1

    return res


def log_activity(
    db: Session,
    tenant_id: str,
    activity_type: str,
    description: str,
    lead_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    sentiment_score: Optional[float] = None,
    performed_by_user_id: Optional[str] = None,
) -> LeadActivity:
    """
    Log an interaction into the activity timeline strictly isolated by tenant_id.
    """
    act = LeadActivity(
        tenant_id=tenant_id,
        activity_type=activity_type,
        description=description,
        lead_id=lead_id,
        customer_id=customer_id,
        sentiment_score=sentiment_score,
        performed_by_user_id=performed_by_user_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(act)
    db.commit()
    db.refresh(act)
    return act


def get_timeline(
    db: Session,
    tenant_id: str,
    customer_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    limit: int = 50,
) -> List[LeadActivity]:
    """
    Fetch timeline activities filtered strictly by tenant_id.
    """
    query = db.query(LeadActivity).filter(LeadActivity.tenant_id == tenant_id)
    if customer_id:
        query = query.filter(LeadActivity.customer_id == customer_id)
    if lead_id:
        query = query.filter(LeadActivity.lead_id == lead_id)
    return query.order_by(LeadActivity.created_at.desc()).limit(limit).all()


def get_crm_stats(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Aggregate statistics for the CRM dashboard with zero cross-tenant leakage.
    """
    from datetime import datetime, timedelta, timezone

    total_customers = db.query(Customer).filter(Customer.tenant_id == tenant_id).count()
    at_risk_customers = db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.risk_score < 0.3
    ).count()

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    new_this_month = db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.created_at >= thirty_days_ago
    ).count()

    total_leads = db.query(Lead).filter(Lead.tenant_id == tenant_id).count()
    won_count = db.query(Lead).filter(Lead.tenant_id == tenant_id, Lead.status == "won").count()
    active_leads = db.query(Lead).filter(Lead.tenant_id == tenant_id, ~Lead.status.in_(["won", "lost"])).count()

    total_deals_value = db.query(func.sum(Lead.estimated_value)).filter(
        Lead.tenant_id == tenant_id
    ).scalar() or 0.0

    won_deals_value = db.query(func.sum(Lead.estimated_value)).filter(
        Lead.tenant_id == tenant_id,
        Lead.status == "won"
    ).scalar() or 0.0

    conversion_rate = round((won_count / total_leads * 100), 1) if total_leads > 0 else 0.0

    total_revenue = db.query(func.sum(Customer.revenue_generated)).filter(
        Customer.tenant_id == tenant_id
    ).scalar() or 0.0

    return {
        "total_customers": total_customers,
        "new_this_month": new_this_month,
        "total_deals_value": float(total_deals_value),
        "won_deals_value": float(won_deals_value),
        "conversion_rate": conversion_rate,
        "at_risk_customers": at_risk_customers,
        "total_leads": total_leads,
        "active_leads": active_leads,
        "total_pipeline_value": float(total_deals_value),
        "won_revenue": float(won_deals_value),
        "total_revenue": float(total_revenue),
        "total_deals": total_leads,
        "deals_value": float(total_deals_value),
    }

