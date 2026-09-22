from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.session import get_db
from core.tenancy import get_current_tenant_id
from services import inventory_service

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================

class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Product or service name")
    sku: Optional[str] = Field(None, description="Optional SKU code. Auto-generated if omitted.")
    description: Optional[str] = Field(None, description="Detailed product description")
    unit_price: float = Field(0.0, ge=0.0, description="Selling price per unit")
    cost_price: float = Field(0.0, ge=0.0, description="Cost price per unit")
    stock_quantity: int = Field(0, ge=0, description="Initial on-hand stock")
    min_stock_threshold: int = Field(10, ge=0, description="Threshold for low-stock warnings")
    category: Optional[str] = Field("General", description="Product category/classification")


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    unit_price: Optional[float] = Field(None, ge=0.0)
    cost_price: Optional[float] = Field(None, ge=0.0)
    min_stock_threshold: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    is_active: Optional[bool] = None


class StockAdjustmentRequest(BaseModel):
    delta: Optional[int] = Field(None, description="Relative quantity adjustment (+/-)")
    new_quantity: Optional[int] = Field(None, ge=0, description="Absolute new stock quantity")


class OrderItemCreate(BaseModel):
    product_id: str = Field(..., description="ID of the catalog product")
    quantity: int = Field(1, ge=1, description="Order quantity")
    unit_price: Optional[float] = Field(None, ge=0.0, description="Custom unit price, defaults to product unit_price")


class OrderCreateRequest(BaseModel):
    customer_id: Optional[str] = Field(None, description="Existing customer ID")
    customer_name: Optional[str] = Field(None, description="Customer name if not selecting ID")
    customer_email: Optional[str] = Field(None, description="Customer email")
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Order line items")
    notes: Optional[str] = Field(None, description="Order notes or instructions")
    status: Optional[str] = Field("pending", description="Initial order status: pending, processing, fulfilled")


class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Target status: pending, processing, fulfilled, cancelled")


# ==============================================================================
# PRODUCT ENDPOINTS
# ==============================================================================

@router.get("/products")
def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    low_stock_only: bool = Query(False, description="Filter only low stock items"),
    search: Optional[str] = Query(None, description="Search by name, SKU, or category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    List catalog products strictly filtered by tenant_id. Zero cross-tenant leakage.
    """
    products, total = inventory_service.get_products(
        db=db,
        tenant_id=tenant_id,
        category=category,
        low_stock_only=low_stock_only,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "products": products,
    }


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product_endpoint(
    req: ProductCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create a new catalog product strictly scoped to tenant_id.
    """
    try:
        product = inventory_service.create_product(
            db=db,
            tenant_id=tenant_id,
            name=req.name,
            sku=req.sku,
            description=req.description,
            unit_price=req.unit_price,
            cost_price=req.cost_price,
            stock_quantity=req.stock_quantity,
            min_stock_threshold=req.min_stock_threshold,
            category=req.category,
        )
        return {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "description": product.description,
            "unit_price": float(product.unit_price),
            "cost_price": float(product.cost_price),
            "stock_quantity": product.stock_quantity,
            "min_stock_threshold": product.min_stock_threshold,
            "category": product.category,
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat() if product.created_at else None,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/products/{product_id}")
def get_product_endpoint(
    product_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get a single product strictly isolated to tenant_id.
    """
    product = inventory_service.get_product_by_id(db, tenant_id=tenant_id, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or unauthorized.")
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "description": product.description,
        "unit_price": float(product.unit_price),
        "cost_price": float(product.cost_price),
        "stock_quantity": product.stock_quantity,
        "min_stock_threshold": product.min_stock_threshold,
        "is_low_stock": product.stock_quantity <= product.min_stock_threshold,
        "category": product.category,
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


@router.patch("/products/{product_id}")
def update_product_endpoint(
    product_id: str,
    req: ProductUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Update catalog product attributes strictly scoped to tenant_id.
    """
    product = inventory_service.update_product(
        db=db,
        tenant_id=tenant_id,
        product_id=product_id,
        name=req.name,
        description=req.description,
        unit_price=req.unit_price,
        cost_price=req.cost_price,
        min_stock_threshold=req.min_stock_threshold,
        category=req.category,
        is_active=req.is_active,
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or unauthorized.")
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "unit_price": float(product.unit_price),
        "cost_price": float(product.cost_price),
        "stock_quantity": product.stock_quantity,
        "min_stock_threshold": product.min_stock_threshold,
        "is_low_stock": product.stock_quantity <= product.min_stock_threshold,
        "category": product.category,
    }


@router.post("/products/{product_id}/adjust-stock")
def adjust_stock_endpoint(
    product_id: str,
    req: StockAdjustmentRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Adjust stock level (delta or new absolute quantity).
    """
    product = inventory_service.adjust_product_stock(
        db=db,
        tenant_id=tenant_id,
        product_id=product_id,
        delta=req.delta,
        new_quantity=req.new_quantity,
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or unauthorized.")
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "stock_quantity": product.stock_quantity,
        "min_stock_threshold": product.min_stock_threshold,
        "is_low_stock": product.stock_quantity <= product.min_stock_threshold,
    }


@router.delete("/products/{product_id}")
def delete_product_endpoint(
    product_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Deactivate product strictly scoped to tenant_id.
    """
    success = inventory_service.delete_product(db, tenant_id=tenant_id, product_id=product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found or unauthorized.")
    return {"message": "Product deactivated successfully."}


# ==============================================================================
# ORDER ENDPOINTS
# ==============================================================================

@router.get("/orders")
def list_orders(
    status: Optional[str] = Query(None, description="pending, processing, fulfilled, cancelled, or all"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    search: Optional[str] = Query(None, description="Search by order number or customer name"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    List orders strictly filtered by tenant_id.
    """
    orders, total = inventory_service.get_orders(
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
        "orders": orders,
    }


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order_endpoint(
    req: OrderCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create a new sales order with line items strictly isolated to tenant_id.
    """
    try:
        items_payload = [itm.model_dump() for itm in req.items]
        order = inventory_service.create_order(
            db=db,
            tenant_id=tenant_id,
            items=items_payload,
            customer_id=req.customer_id,
            customer_name=req.customer_name,
            customer_email=req.customer_email,
            notes=req.notes,
            status=req.status or "pending",
        )
        return inventory_service.get_order_by_id(db, tenant_id=tenant_id, order_id=order.id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/orders/{order_id}")
def get_order_endpoint(
    order_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get single order with items and product details strictly isolated to tenant_id.
    """
    order = inventory_service.get_order_by_id(db, tenant_id=tenant_id, order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or unauthorized.")
    return order


@router.patch("/orders/{order_id}/status")
def update_order_status_endpoint(
    order_id: str,
    req: OrderStatusUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Update order status. Automatically decrements product stock upon fulfillment!
    """
    try:
        order = inventory_service.update_order_status(
            db=db,
            tenant_id=tenant_id,
            order_id=order_id,
            status=req.status,
        )
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or unauthorized.")
        return inventory_service.get_order_by_id(db, tenant_id=tenant_id, order_id=order.id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/orders/{order_id}/convert-to-invoice")
def convert_to_invoice_endpoint(
    order_id: str,
    tax_rate: float = Query(10.0, ge=0.0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Convert an Order into an Invoice in the Billing module with PDF generation.
    """
    try:
        invoice = inventory_service.convert_order_to_invoice(
            db=db,
            tenant_id=tenant_id,
            order_id=order_id,
            tax_rate=tax_rate,
        )
        return {
            "message": "Order converted to invoice successfully.",
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "total_amount": float(invoice.total_amount),
            "status": invoice.status,
            "pdf_url": invoice.pdf_url,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/stats")
def inventory_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Aggregate inventory, stock valuations, and order stats strictly filtered by tenant_id.
    """
    return inventory_service.get_inventory_stats(db, tenant_id=tenant_id)
