from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.session import get_db
from core.tenancy import get_current_tenant_id
from services import crm_service
from ai.crm_ai import calculate_risk_score, generate_forecast, generate_customer_summary

router = APIRouter(prefix="/crm", tags=["CRM"])


# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================

class CustomerCreateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = "manual"
    notes: Optional[str] = None
    tags: Optional[str] = None


class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    risk_score: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class LeadCreateRequest(BaseModel):
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = "new"
    estimated_value: Optional[float] = 0.00
    probability: Optional[int] = 20
    source: Optional[str] = "web"
    customer_id: Optional[str] = None
    notes: Optional[str] = None


class LeadUpdateRequest(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    estimated_value: Optional[float] = None
    probability: Optional[int] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    customer_id: Optional[str] = None


class ActivityCreateRequest(BaseModel):
    activity_type: str = Field(..., description="call, email, meeting, note, status_change")
    description: str
    sentiment_score: Optional[float] = None
    lead_id: Optional[str] = None


class CustomerNotesRequest(BaseModel):
    notes: str


class CustomerTagsRequest(BaseModel):
    tags: str


# Legacy compatibility schema for Deals
class DealRequest(BaseModel):
    customer_id: Optional[str] = None
    title: str
    value: float
    stage: str = "lead"
    probability: int = 50
    expected_close: Optional[str] = None
    notes: Optional[str] = None


# ==============================================================================
# CUSTOMER ENDPOINTS
# ==============================================================================

@router.get("/customers")
def list_customers(
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    List customers strictly filtered by tenant_id. Zero cross-tenant leakage.
    """
    customers = crm_service.get_customers(
        db=db, tenant_id=tenant_id, search=search, status=status, limit=limit, offset=offset
    )
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "company": c.company,
            "source": c.source,
            "status": c.status,
            "risk_score": c.risk_score,
            "total_conversations": c.total_conversations,
            "avg_sentiment": c.avg_sentiment,
            "total_tickets": c.total_tickets,
            "revenue_generated": float(c.revenue_generated),
            "notes": c.notes,
            "tags": c.tags,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in customers
    ]


@router.post("/customers")
def create_customer_endpoint(
    req: CustomerCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create customer associated with the tenant.
    """
    customer = crm_service.create_customer(
        db=db,
        tenant_id=tenant_id,
        name=req.name,
        email=req.email,
        phone=req.phone,
        company=req.company,
        source=req.source or "manual",
        notes=req.notes,
        tags=req.tags,
    )
    return {
        "message": "Customer created successfully",
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "status": customer.status,
        },
        "id": customer.id,
        "customer_id": customer.id,
        "created": True,
    }


@router.get("/customers/{customer_id}")
def get_customer_endpoint(
    customer_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Fetch a single customer for the tenant.
    """
    customer = crm_service.get_customer_by_id(db, tenant_id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found or access denied")
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "company": customer.company,
        "source": customer.source,
        "status": customer.status,
        "risk_score": customer.risk_score,
        "notes": customer.notes,
        "tags": customer.tags,
        "revenue_generated": float(customer.revenue_generated),
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
    }


@router.put("/customers/{customer_id}")
def update_customer_endpoint(
    customer_id: str,
    req: CustomerUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Update customer details ensuring tenant isolation.
    """
    customer = crm_service.update_customer(
        db=db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        data=req.model_dump(exclude_unset=True),
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found or access denied")
    return {"success": True, "message": "Customer updated"}


@router.delete("/customers/{customer_id}")
def delete_customer_endpoint(
    customer_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Delete customer with tenant isolation.
    """
    success = crm_service.delete_customer(db, tenant_id, customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found or access denied")
    return {"success": True, "message": "Customer deleted"}


@router.get("/customers/{customer_id}/profile")
def get_customer_full_profile_endpoint(
    customer_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Comprehensive customer profile with activity timeline, deals, tickets.
    """
    profile = crm_service.get_customer_profile(db, tenant_id, customer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Customer not found or access denied")
    return profile


@router.get("/customers/{customer_id}/timeline")
def get_customer_timeline_endpoint(
    customer_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Fetch customer activity timeline.
    """
    timeline = crm_service.get_timeline(db, tenant_id, customer_id=customer_id)
    return [
        {
            "id": a.id,
            "type": a.activity_type,
            "description": a.description,
            "sentiment_score": a.sentiment_score,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in timeline
    ]


@router.post("/customers/{customer_id}/activities")
def add_customer_activity(
    customer_id: str,
    req: ActivityCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Log an interaction activity into customer timeline.
    """
    customer = crm_service.get_customer_by_id(db, tenant_id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    act = crm_service.log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type=req.activity_type,
        description=req.description,
        customer_id=customer_id,
        lead_id=req.lead_id,
        sentiment_score=req.sentiment_score,
    )
    return {"message": "Activity logged", "id": act.id}


@router.post("/customers/{customer_id}/update-notes")
def update_customer_notes(
    customer_id: str,
    req: CustomerNotesRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    customer = crm_service.update_customer(db, tenant_id, customer_id, {"notes": req.notes})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"success": True}


@router.post("/customers/{customer_id}/update-tags")
def update_customer_tags(
    customer_id: str,
    req: CustomerTagsRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    customer = crm_service.update_customer(db, tenant_id, customer_id, {"tags": req.tags})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"success": True}


# ==============================================================================
# LEAD ENDPOINTS (STATUS PIPELINE & KANBAN)
# ==============================================================================

@router.get("/leads")
def list_leads(
    status: Optional[str] = Query(None, description="Filter by stage: new, contacted, qualified, proposal, won, lost"),
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    List sales leads strictly filtered by tenant_id.
    """
    leads = crm_service.get_leads(
        db=db, tenant_id=tenant_id, status=status, search=search, limit=limit, offset=offset
    )
    return [
        {
            "id": l.id,
            "title": l.title,
            "name": l.name,
            "company": l.company,
            "email": l.email,
            "phone": l.phone,
            "status": l.status,
            "estimated_value": float(l.estimated_value),
            "probability": l.probability,
            "source": l.source,
            "customer_id": l.customer_id,
            "notes": l.notes,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in leads
    ]


@router.post("/leads")
def create_lead_endpoint(
    req: LeadCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create a new sales lead.
    """
    lead = crm_service.create_lead(
        db=db,
        tenant_id=tenant_id,
        name=req.name,
        title=req.title,
        email=req.email,
        phone=req.phone,
        company=req.company,
        status=req.status or "new",
        estimated_value=req.estimated_value or 0.00,
        probability=req.probability or 20,
        source=req.source or "web",
        customer_id=req.customer_id,
        notes=req.notes,
    )
    return {
        "message": "Lead created successfully",
        "lead": {
            "id": lead.id,
            "title": lead.title,
            "name": lead.name,
            "status": lead.status,
            "estimated_value": float(lead.estimated_value),
        },
        "id": lead.id,
    }


@router.get("/leads/{lead_id}")
def get_lead_endpoint(
    lead_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get a single lead by ID ensuring tenant ownership.
    """
    lead = crm_service.get_lead_by_id(db, tenant_id, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or access denied")
    return {
        "id": lead.id,
        "title": lead.title,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "company": lead.company,
        "status": lead.status,
        "estimated_value": float(lead.estimated_value),
        "probability": lead.probability,
        "source": lead.source,
        "customer_id": lead.customer_id,
        "notes": lead.notes,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


@router.put("/leads/{lead_id}")
def update_lead_endpoint(
    lead_id: str,
    req: LeadUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Update lead details or move stage across the Kanban board.
    """
    lead = crm_service.update_lead(
        db=db,
        tenant_id=tenant_id,
        lead_id=lead_id,
        data=req.model_dump(exclude_unset=True),
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found or access denied")
    return {
        "success": True,
        "message": f"Lead updated. Current status: {lead.status}",
        "lead": {
            "id": lead.id,
            "status": lead.status,
            "estimated_value": float(lead.estimated_value),
        }
    }


@router.delete("/leads/{lead_id}")
def delete_lead_endpoint(
    lead_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Delete a lead ensuring tenant isolation.
    """
    success = crm_service.delete_lead(db, tenant_id, lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found or access denied")
    return {"success": True, "message": "Lead deleted"}


@router.post("/leads/{lead_id}/convert")
def convert_lead_endpoint(
    lead_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Convert a won lead to an active paying customer!
    """
    customer = crm_service.convert_lead_to_customer(db, tenant_id, lead_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Lead not found or cannot be converted")
    return {
        "message": "Lead successfully converted to Customer!",
        "customer_id": customer.id,
        "customer_name": customer.name,
        "status": customer.status,
    }


# ==============================================================================
# PIPELINE KANBAN & DEALS COMPATIBILITY
# ==============================================================================

@router.get("/pipeline")
def get_pipeline_endpoint(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Retrieve Kanban pipeline board grouped by stage for the tenant.
    """
    return crm_service.get_crm_pipeline(db, tenant_id)


# Legacy /deals alias for existing frontend compatibility
@router.get("/deals")
def list_deals_alias(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    leads = crm_service.get_leads(db, tenant_id)
    return [
        {
            "id": l.id,
            "title": l.title or l.name,
            "customer_name": l.name,
            "customer_id": l.customer_id,
            "value": float(l.estimated_value),
            "stage": l.status,
            "probability": l.probability,
            "expected_close": l.created_at.isoformat() if l.created_at else None,
        }
        for l in leads
    ]


@router.post("/deals")
def create_deal_alias(
    req: DealRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    lead = crm_service.create_lead(
        db=db,
        tenant_id=tenant_id,
        name=req.title,
        title=req.title,
        estimated_value=req.value,
        status=req.stage,
        probability=req.probability,
        customer_id=str(req.customer_id) if req.customer_id else None,
        notes=req.notes,
    )
    return {"id": lead.id, "success": True}


@router.put("/deals/{did}")
def update_deal_alias(
    did: str,
    req: Dict[str, Any],
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    lead = crm_service.update_lead(db, tenant_id, did, req)
    if not lead:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"success": True}


@router.delete("/deals/{did}")
def delete_deal_alias(
    did: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    success = crm_service.delete_lead(db, tenant_id, did)
    if not success:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"success": True}


# ==============================================================================
# STATS & AI ANALYTICS
# ==============================================================================

@router.get("/stats")
def crm_stats_endpoint(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    CRM metrics and pipeline summary for authenticated tenant.
    """
    return crm_service.get_crm_stats(db, tenant_id)


@router.post("/customers/{cid}/summary")
def customer_ai_summary(
    cid: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Generate AI summary of customer profile and timeline.
    """
    customer = crm_service.get_customer_by_id(db, tenant_id, cid)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    timeline = crm_service.get_timeline(db, tenant_id, customer_id=cid)

    c_dict = {
        "name": customer.name,
        "company": customer.company,
        "avg_sentiment": customer.avg_sentiment,
        "total_tickets": customer.total_tickets,
        "total_conversations": customer.total_conversations,
        "revenue_generated": float(customer.revenue_generated),
    }
    t_list = [{"type": a.activity_type, "description": a.description} for a in timeline]
    return generate_customer_summary(c_dict, t_list)


@router.post("/customers/{cid}/risk-score")
def customer_ai_risk(
    cid: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Calculate customer churn risk score via AI.
    """
    customer = crm_service.get_customer_by_id(db, tenant_id, cid)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    timeline = crm_service.get_timeline(db, tenant_id, customer_id=cid)

    c_dict = {
        "name": customer.name,
        "avg_sentiment": customer.avg_sentiment,
        "total_tickets": customer.total_tickets,
    }
    t_list = [{"type": a.activity_type, "description": a.description} for a in timeline]
    result = calculate_risk_score(c_dict, t_list)

    if "risk_score" in result:
        crm_service.update_customer(db, tenant_id, cid, {"risk_score": result["risk_score"]})
    return result
