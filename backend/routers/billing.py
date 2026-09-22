import os
from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.session import get_db
from core.tenancy import get_current_tenant_id
from services import billing_service
from services.billing_scheduler import run_billing_check_now

router = APIRouter(prefix="/billing", tags=["Billing"])


# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================

class InvoiceItemCreate(BaseModel):
    description: str = Field(..., min_length=1, description="Item or service description")
    quantity: int = Field(1, ge=1, description="Quantity")
    unit_price: float = Field(..., ge=0.0, description="Unit price per item")
    product_id: Optional[str] = Field(None, description="Optional linked product ID")


class InvoiceCreateRequest(BaseModel):
    customer_id: Optional[str] = Field(None, description="Existing customer ID")
    customer_name: Optional[str] = Field(None, description="Customer name if not selecting existing ID")
    customer_email: Optional[str] = Field(None, description="Customer email")
    issue_date: Optional[date] = Field(None, description="Date of issue, defaults to today")
    due_date: Optional[date] = Field(None, description="Due date, defaults to issue_date + 30 days")
    items: List[InvoiceItemCreate] = Field(..., min_items=1, description="Line items for the invoice")
    tax_rate: Optional[float] = Field(0.0, ge=0.0, description="Tax rate percentage (e.g. 10 for 10%)")
    tax_amount: Optional[float] = Field(None, ge=0.0, description="Fixed tax amount (overrides tax_rate if provided)")
    discount_amount: Optional[float] = Field(0.0, ge=0.0, description="Flat discount amount")
    notes: Optional[str] = Field(None, description="Payment instructions or customer notes")
    status: Optional[str] = Field("pending", description="Initial status: draft or pending")
    auto_generate_pdf: Optional[bool] = Field(True, description="Whether to automatically generate ReportLab PDF")


class InvoiceStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Target status: draft, pending, paid, overdue, cancelled")


# ==============================================================================
# INVOICE ENDPOINTS
# ==============================================================================

@router.get("/invoices")
def list_invoices(
    status: Optional[str] = Query(None, description="Filter: draft, pending, paid, overdue, cancelled, or all"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    search: Optional[str] = Query(None, description="Search by invoice number or customer name"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    List invoices strictly filtered by tenant_id. Zero cross-tenant leakage.
    """
    items, total = billing_service.get_invoices(
        db=db,
        tenant_id=tenant_id,
        status=status,
        customer_id=customer_id,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "invoices": items,
    }


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
def create_invoice_endpoint(
    req: InvoiceCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create a new invoice with line items, calculating totals and generating PDF.
    Strictly isolated to current tenant.
    """
    try:
        items_payload = [item.model_dump() for item in req.items]
        invoice = billing_service.create_invoice(
            db=db,
            tenant_id=tenant_id,
            items=items_payload,
            customer_id=req.customer_id,
            customer_name=req.customer_name,
            customer_email=req.customer_email,
            issue_date=req.issue_date,
            due_date=req.due_date,
            tax_rate=req.tax_rate or 0.0,
            tax_amount=req.tax_amount,
            discount_amount=req.discount_amount or 0.0,
            notes=req.notes,
            status=req.status or "pending",
            auto_generate_pdf=req.auto_generate_pdf if req.auto_generate_pdf is not None else True,
        )
        return billing_service.get_invoice_by_id(db, tenant_id=tenant_id, invoice_id=invoice.id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")


@router.get("/invoices/{invoice_id}")
def get_invoice_detail(
    invoice_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Retrieve single invoice with all line items strictly scoped to tenant_id.
    """
    inv = billing_service.get_invoice_by_id(db, tenant_id=tenant_id, invoice_id=invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found or unauthorized.")
    return inv


@router.patch("/invoices/{invoice_id}/status")
def update_invoice_status_endpoint(
    invoice_id: str,
    req: InvoiceStatusUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Update invoice status (e.g. mark as paid, cancelled, overdue).
    Syncs customer revenue and regenerates PDF stamp.
    """
    try:
        updated = billing_service.update_invoice_status(
            db=db,
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            status=req.status,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Invoice not found or unauthorized.")
        return billing_service.get_invoice_by_id(db, tenant_id=tenant_id, invoice_id=invoice_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/invoices/{invoice_id}/pdf")
def get_invoice_pdf(
    invoice_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Download or stream the generated ReportLab PDF for the invoice.
    Strictly tenant isolated.
    """
    file_path = billing_service.get_invoice_pdf_path(db, tenant_id=tenant_id, invoice_id=invoice_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Invoice PDF not found or unauthorized.")

    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.post("/invoices/{invoice_id}/regenerate-pdf")
def regenerate_invoice_pdf_endpoint(
    invoice_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Force regeneration of PDF file for invoice.
    """
    inv = db.query(billing_service.Invoice).filter(
        billing_service.Invoice.tenant_id == tenant_id,
        billing_service.Invoice.id == invoice_id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    file_path, web_url = billing_service.generate_and_save_invoice_pdf(db, inv)
    inv.pdf_url = web_url
    db.commit()

    return {"message": "PDF regenerated successfully", "pdf_url": web_url}


@router.delete("/invoices/{invoice_id}")
def delete_invoice_endpoint(
    invoice_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Delete invoice and its line items strictly isolated to tenant_id.
    """
    success = billing_service.delete_invoice(db, tenant_id=tenant_id, invoice_id=invoice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invoice not found or unauthorized.")
    return {"message": "Invoice deleted successfully."}


@router.get("/stats")
def billing_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Aggregate billing KPIs strictly filtered by tenant_id.
    """
    return billing_service.get_billing_stats(db, tenant_id=tenant_id)


@router.post("/reminders/trigger")
def trigger_overdue_check_endpoint(
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Manually trigger overdue check and reminder scanner for this tenant.
    """
    updated = run_billing_check_now(tenant_id=tenant_id)
    return {
        "message": f"Overdue check completed. {len(updated)} invoice(s) updated.",
        "updated_invoices": updated,
    }
