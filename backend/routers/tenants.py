import re
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.session import get_db
from db.models import Tenant
from core.tenancy import get_current_tenant_id, get_or_create_default_tenant

router = APIRouter(prefix="/tenants", tags=["Tenancy"])


class TenantCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Organization / Company Name")
    slug: Optional[str] = Field(None, description="URL-safe unique identifier. Auto-generated from name if omitted.")


@router.get("")
def list_tenants(db: Session = Depends(get_db)):
    """
    List all active organizations in the BMS system.
    """
    # Ensure default tenant exists
    get_or_create_default_tenant(db)
    tenants = db.query(Tenant).filter(Tenant.is_active == True).order_by(Tenant.created_at.asc()).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "slug": t.slug,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tenants
    ]


@router.get("/current")
def get_current_tenant_info(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get metadata for the currently authenticated organization.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Current tenant not found.")
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "is_active": tenant.is_active,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_tenant_endpoint(
    req: TenantCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Provision a brand new isolated tenant organization with its own independent workspace.
    """
    raw_slug = req.slug or req.name.lower()
    clean_slug = re.sub(r"[^a-z0-9]+", "-", raw_slug.lower()).strip("-")
    if not clean_slug:
        clean_slug = "org"

    # Ensure unique slug
    candidate = clean_slug
    seq = 1
    while db.query(Tenant.id).filter(Tenant.slug == candidate).first():
        candidate = f"{clean_slug}-{seq}"
        seq += 1

    tenant = Tenant(
        name=req.name.strip(),
        slug=candidate,
        is_active=True,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "is_active": tenant.is_active,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
    }
