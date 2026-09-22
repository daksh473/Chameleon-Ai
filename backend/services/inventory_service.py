from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from db.models import Product, Order, OrderItem, Customer, Invoice
from services import billing_service


# ==============================================================================
# SKU & ORDER NUMBER GENERATORS
# ==============================================================================

def generate_sku(db: Session, tenant_id: str, prefix: str = "PRD") -> str:
    """
    Generate sequential SKU: PRD-XXXX scoped strictly by tenant_id.
    """
    count = db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.sku.like(f"{prefix}-%")
    ).count()

    seq = count + 1
    while True:
        candidate = f"{prefix}-{seq:04d}"
        exists = db.query(Product.id).filter(
            Product.tenant_id == tenant_id,
            Product.sku == candidate
        ).first()
        if not exists:
            return candidate
        seq += 1


def generate_order_number(db: Session, tenant_id: str) -> str:
    """
    Generate sequential order number: ORD-YYYY-XXXX scoped strictly by tenant_id.
    """
    current_year = datetime.now().year
    prefix = f"ORD-{current_year}-"

    count = db.query(Order).filter(
        Order.tenant_id == tenant_id,
        Order.order_number.like(f"{prefix}%")
    ).count()

    seq = count + 1
    while True:
        candidate = f"{prefix}{seq:04d}"
        exists = db.query(Order.id).filter(
            Order.tenant_id == tenant_id,
            Order.order_number == candidate
        ).first()
        if not exists:
            return candidate
        seq += 1


# ==============================================================================
# PRODUCT OPERATIONS
# ==============================================================================

def create_product(
    db: Session,
    tenant_id: str,
    name: str,
    sku: Optional[str] = None,
    description: Optional[str] = None,
    unit_price: float = 0.0,
    cost_price: float = 0.0,
    stock_quantity: int = 0,
    min_stock_threshold: int = 10,
    category: Optional[str] = None,
) -> Product:
    """
    Create a new catalog product strictly tied to tenant_id.
    """
    if not sku:
        sku = generate_sku(db, tenant_id)
    else:
        sku = sku.strip().upper()
        exists = db.query(Product.id).filter(
            Product.tenant_id == tenant_id,
            Product.sku == sku
        ).first()
        if exists:
            raise ValueError(f"SKU '{sku}' already exists for this tenant.")

    product = Product(
        tenant_id=tenant_id,
        name=name.strip(),
        sku=sku,
        description=description,
        unit_price=round(float(unit_price), 2),
        cost_price=round(float(cost_price), 2),
        stock_quantity=int(stock_quantity),
        min_stock_threshold=int(min_stock_threshold),
        category=category.strip() if category else "General",
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_products(
    db: Session,
    tenant_id: str,
    category: Optional[str] = None,
    low_stock_only: bool = False,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List products strictly filtered by tenant_id.
    Zero cross-tenant leakage.
    """
    query = db.query(Product).filter(Product.tenant_id == tenant_id, Product.is_active == True)

    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(category))

    if low_stock_only:
        query = query.filter(Product.stock_quantity <= Product.min_stock_threshold)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.sku.ilike(search_term),
                Product.category.ilike(search_term),
            )
        )

    total_count = query.count()
    products = query.order_by(Product.name.asc()).offset(offset).limit(limit).all()

    results = []
    for p in products:
        results.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "description": p.description,
            "unit_price": float(p.unit_price),
            "cost_price": float(p.cost_price),
            "stock_quantity": p.stock_quantity,
            "min_stock_threshold": p.min_stock_threshold,
            "is_low_stock": p.stock_quantity <= p.min_stock_threshold,
            "category": p.category,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })

    return results, total_count


def get_product_by_id(db: Session, tenant_id: str, product_id: str) -> Optional[Product]:
    """
    Get single product strictly isolated to tenant_id.
    """
    return db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.id == product_id
    ).first()


def update_product(
    db: Session,
    tenant_id: str,
    product_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    unit_price: Optional[float] = None,
    cost_price: Optional[float] = None,
    min_stock_threshold: Optional[int] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[Product]:
    """
    Update catalog product attributes strictly scoped to tenant_id.
    """
    product = get_product_by_id(db, tenant_id, product_id)
    if not product:
        return None

    if name is not None:
        product.name = name.strip()
    if description is not None:
        product.description = description
    if unit_price is not None:
        product.unit_price = round(float(unit_price), 2)
    if cost_price is not None:
        product.cost_price = round(float(cost_price), 2)
    if min_stock_threshold is not None:
        product.min_stock_threshold = int(min_stock_threshold)
    if category is not None:
        product.category = category.strip()
    if is_active is not None:
        product.is_active = is_active

    db.commit()
    db.refresh(product)
    return product


def adjust_product_stock(
    db: Session,
    tenant_id: str,
    product_id: str,
    delta: Optional[int] = None,
    new_quantity: Optional[int] = None,
) -> Optional[Product]:
    """
    Adjust product stock quantity with safety checks against negative stock.
    """
    product = get_product_by_id(db, tenant_id, product_id)
    if not product:
        return None

    if new_quantity is not None:
        product.stock_quantity = max(0, int(new_quantity))
    elif delta is not None:
        product.stock_quantity = max(0, product.stock_quantity + int(delta))

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, tenant_id: str, product_id: str) -> bool:
    """
    Soft delete or delete product strictly scoped to tenant_id.
    """
    product = get_product_by_id(db, tenant_id, product_id)
    if not product:
        return False

    product.is_active = False
    db.commit()
    return True


# ==============================================================================
# ORDER & FULFILLMENT OPERATIONS
# ==============================================================================

def create_order(
    db: Session,
    tenant_id: str,
    items: List[Dict[str, Any]],
    customer_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
    notes: Optional[str] = None,
    status: str = "pending",
) -> Order:
    """
    Create a new sales order with line items strictly tied to tenant_id.
    If created with status 'fulfilled', automatically decrements product stock.
    """
    if not items:
        raise ValueError("At least one line item is required to create an order.")

    # Auto-resolve customer if name provided
    if not customer_id and customer_name:
        cust = db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            or_(Customer.name == customer_name, Customer.email == customer_email)
        ).first()
        if not cust:
            cust = Customer(
                tenant_id=tenant_id,
                name=customer_name,
                email=customer_email,
                status="active"
            )
            db.add(cust)
            db.commit()
            db.refresh(cust)
        customer_id = cust.id
    elif customer_id:
        cust = db.query(Customer).filter(Customer.tenant_id == tenant_id, Customer.id == customer_id).first()
        if not cust:
            raise ValueError(f"Customer {customer_id} does not exist in this tenant.")

    # Validate items and products
    total_amount = 0.0
    validated_items = []
    for itm in items:
        pid = itm.get("product_id")
        if not pid:
            raise ValueError("Every order line item must have a product_id.")
        product = get_product_by_id(db, tenant_id, pid)
        if not product:
            raise ValueError(f"Product {pid} not found in this tenant.")

        qty = int(itm.get("quantity", 1))
        if qty <= 0:
            qty = 1

        price = float(itm.get("unit_price") if itm.get("unit_price") is not None else product.unit_price)
        line_total = round(qty * price, 2)
        total_amount += line_total

        validated_items.append({
            "product": product,
            "product_id": pid,
            "quantity": qty,
            "unit_price": price,
            "total_amount": line_total,
        })

    order_num = generate_order_number(db, tenant_id)
    order_status = status.lower()
    is_fulfilled = order_status == "fulfilled"

    order = Order(
        tenant_id=tenant_id,
        customer_id=customer_id,
        order_number=order_num,
        status=order_status,
        total_amount=round(total_amount, 2),
        notes=notes,
        fulfilled_at=datetime.now(timezone.utc) if is_fulfilled else None,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Insert order items and optionally decrement stock if fulfilled immediately
    for vi in validated_items:
        oi = OrderItem(
            tenant_id=tenant_id,
            order_id=order.id,
            product_id=vi["product_id"],
            quantity=vi["quantity"],
            unit_price=vi["unit_price"],
            total_amount=vi["total_amount"],
        )
        db.add(oi)

        if is_fulfilled:
            prod = vi["product"]
            prod.stock_quantity = max(0, prod.stock_quantity - vi["quantity"])

    db.commit()
    db.refresh(order)
    return order


def get_orders(
    db: Session,
    tenant_id: str,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List orders strictly filtered by tenant_id.
    Zero cross-tenant leakage.
    """
    query = db.query(Order).filter(Order.tenant_id == tenant_id)

    if status and status.lower() != "all":
        query = query.filter(Order.status == status.lower())

    if customer_id:
        query = query.filter(Order.customer_id == customer_id)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.outerjoin(Customer, Order.customer_id == Customer.id).filter(
            or_(
                Order.order_number.ilike(search_term),
                Customer.name.ilike(search_term),
                Customer.email.ilike(search_term),
            )
        )

    total_count = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for o in orders:
        cust = o.customer
        results.append({
            "id": o.id,
            "order_number": o.order_number,
            "customer_id": o.customer_id,
            "customer_name": cust.name if cust else "Direct / Unregistered",
            "customer_email": cust.email if cust else None,
            "status": o.status,
            "total_amount": float(o.total_amount),
            "items_count": len(o.items),
            "fulfilled_at": o.fulfilled_at.isoformat() if o.fulfilled_at else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })

    return results, total_count


def get_order_by_id(db: Session, tenant_id: str, order_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve single order with line items and product details strictly scoped to tenant_id.
    """
    order = db.query(Order).filter(
        Order.tenant_id == tenant_id,
        Order.id == order_id
    ).first()

    if not order:
        return None

    cust = order.customer
    items = []
    for itm in order.items:
        prod = itm.product
        items.append({
            "id": itm.id,
            "product_id": itm.product_id,
            "product_name": prod.name if prod else "Unknown Product",
            "product_sku": prod.sku if prod else "N/A",
            "quantity": itm.quantity,
            "unit_price": float(itm.unit_price),
            "total_amount": float(itm.total_amount),
            "current_stock": prod.stock_quantity if prod else 0,
        })

    return {
        "id": order.id,
        "tenant_id": order.tenant_id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "customer": {
            "id": cust.id,
            "name": cust.name,
            "email": cust.email,
            "phone": cust.phone,
            "company": cust.company,
        } if cust else None,
        "status": order.status,
        "total_amount": float(order.total_amount),
        "notes": order.notes,
        "fulfilled_at": order.fulfilled_at.isoformat() if order.fulfilled_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "items": items,
    }


def update_order_status(
    db: Session,
    tenant_id: str,
    order_id: str,
    status: str,
) -> Optional[Order]:
    """
    Update order status with automatic stock adjustments:
    - If status changes to 'fulfilled': decrements product stock for each line item.
    - If status was 'fulfilled' and changes to 'cancelled': restores product stock.
    """
    valid_statuses = {"pending", "processing", "fulfilled", "cancelled"}
    new_status = status.lower()
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")

    order = db.query(Order).filter(
        Order.tenant_id == tenant_id,
        Order.id == order_id
    ).first()

    if not order:
        return None

    old_status = order.status
    if old_status == new_status:
        return order

    # Handle stock movements
    if old_status != "fulfilled" and new_status == "fulfilled":
        # Decrement stock for all items
        for itm in order.items:
            prod = itm.product
            if prod:
                prod.stock_quantity = max(0, prod.stock_quantity - itm.quantity)
        order.fulfilled_at = datetime.now(timezone.utc)

    elif old_status == "fulfilled" and new_status == "cancelled":
        # Restore stock for all items
        for itm in order.items:
            prod = itm.product
            if prod:
                prod.stock_quantity = prod.stock_quantity + itm.quantity
        order.fulfilled_at = None

    order.status = new_status
    db.commit()
    db.refresh(order)
    return order


def convert_order_to_invoice(
    db: Session,
    tenant_id: str,
    order_id: str,
    tax_rate: float = 10.0,
) -> Invoice:
    """
    Seamless link to Billing Module:
    Converts an Order into a full Invoice with line items and generated PDF.
    """
    order = db.query(Order).filter(
        Order.tenant_id == tenant_id,
        Order.id == order_id
    ).first()

    if not order:
        raise ValueError(f"Order {order_id} not found in this tenant.")

    items_payload = [
        {
            "product_id": itm.product_id,
            "description": f"{itm.product.name} (SKU: {itm.product.sku})" if itm.product else "Order Item",
            "quantity": itm.quantity,
            "unit_price": float(itm.unit_price),
        }
        for itm in order.items
    ]

    invoice = billing_service.create_invoice(
        db=db,
        tenant_id=tenant_id,
        customer_id=order.customer_id,
        items=items_payload,
        tax_rate=tax_rate,
        notes=f"Generated from Order #{order.order_number}. {order.notes or ''}".strip(),
        status="paid" if order.status == "fulfilled" else "pending",
        auto_generate_pdf=True,
    )

    return invoice


# ==============================================================================
# INVENTORY KPIS & METRICS
# ==============================================================================

def get_inventory_stats(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Compute inventory and fulfillment metrics strictly scoped by tenant_id.
    """
    active_products = db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.is_active == True
    ).all()

    total_products = len(active_products)
    low_stock_count = sum(1 for p in active_products if p.stock_quantity <= p.min_stock_threshold)
    out_of_stock_count = sum(1 for p in active_products if p.stock_quantity == 0)

    total_inventory_value = sum(p.stock_quantity * float(p.unit_price) for p in active_products)
    total_inventory_cost = sum(p.stock_quantity * float(p.cost_price) for p in active_products)

    total_orders = db.query(Order).filter(Order.tenant_id == tenant_id).count()
    pending_orders = db.query(Order).filter(Order.tenant_id == tenant_id, Order.status == "pending").count()
    processing_orders = db.query(Order).filter(Order.tenant_id == tenant_id, Order.status == "processing").count()
    fulfilled_orders = db.query(Order).filter(Order.tenant_id == tenant_id, Order.status == "fulfilled").count()

    total_fulfilled_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.tenant_id == tenant_id,
        Order.status == "fulfilled"
    ).scalar() or 0.0

    return {
        "total_products": total_products,
        "low_stock_items": low_stock_count,
        "out_of_stock_items": out_of_stock_count,
        "total_inventory_value": round(float(total_inventory_value), 2),
        "total_inventory_cost": round(float(total_inventory_cost), 2),
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "fulfilled_orders": fulfilled_orders,
        "total_fulfilled_revenue": round(float(total_fulfilled_revenue), 2),
    }
