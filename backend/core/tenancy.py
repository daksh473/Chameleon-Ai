import os
from typing import Optional
from fastapi import Header, Query, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from db.models import Tenant

DEFAULT_TENANT_SLUG = os.getenv("DEFAULT_TENANT_SLUG", "default")
DEFAULT_TENANT_NAME = os.getenv("DEFAULT_TENANT_NAME", "Default Organization")


def get_or_create_default_tenant(db: Session) -> Tenant:
    """
    Ensures a default tenant exists in the database for fallback/system events.
    """
    tenant = db.query(Tenant).filter(Tenant.slug == DEFAULT_TENANT_SLUG).first()
    if not tenant:
        tenant = Tenant(
            name=DEFAULT_TENANT_NAME,
            slug=DEFAULT_TENANT_SLUG,
            is_active=True,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


def get_current_tenant_id(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    tenant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> str:
    """
    Dependency that enforces tenant isolation.
    Extracts tenant_id from header, query param, or falls back to default tenant.
    Verifies that the tenant exists and is active.
    """
    resolved_id = x_tenant_id or tenant_id

    if resolved_id:
        tenant = db.query(Tenant).filter(Tenant.id == resolved_id).first()
        if not tenant:
            # Check by slug as a fallback convenience
            tenant = db.query(Tenant).filter(Tenant.slug == resolved_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant '{resolved_id}' not found.")
        if not tenant.is_active:
            raise HTTPException(status_code=403, detail="Tenant is deactivated.")
        return tenant.id

    # Fallback to default tenant
    default_tenant = get_or_create_default_tenant(db)
    return default_tenant.id
