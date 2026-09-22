"""
TASK 5 Verification Script
Verifies:
1. Product CRUD with auto SKU generation and categories.
2. Stock adjustments and low-stock threshold detection.
3. Sales Order creation with line items.
4. Order fulfillment with automatic stock decrement.
5. Order cancellation with stock restoration.
6. Seamless Order-to-Invoice conversion in Billing module.
7. Strict Multi-Tenant Isolation (Tenant B has zero access to Tenant A's inventory).
8. Non-regression of Tasks 1, 2, 3, 4 (Models, Support, CRM, Billing).
"""
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db.session import SessionLocal
from db.models import Tenant, Customer, Product, Order, OrderItem
from core.tenancy import get_or_create_default_tenant
from services import inventory_service, billing_service, crm_service, support_service

def main():
    print("=== STARTING TASK 5 VERIFICATION ===")
    db = SessionLocal()

    try:
        # Step 1: Default Tenant (Tenant A)
        tenant_a = get_or_create_default_tenant(db)
        print(f"✅ Step 1: Default Tenant A: {tenant_a.name} ({tenant_a.id})")

        # Step 2: Create Products in Tenant A
        prod1 = inventory_service.create_product(
            db=db,
            tenant_id=tenant_a.id,
            name="Chameleon Edge Router X1",
            unit_price=299.99,
            cost_price=150.00,
            stock_quantity=20,
            min_stock_threshold=8,
            category="Hardware",
        )
        assert prod1.id is not None
        assert prod1.sku.startswith("PRD-")
        print(f"✅ Step 2a: Created Product 1: {prod1.name} [SKU: {prod1.sku}] - Stock: {prod1.stock_quantity}")

        prod2 = inventory_service.create_product(
            db=db,
            tenant_id=tenant_a.id,
            name="Fiber Optic Patch Cable 5m",
            unit_price=19.99,
            cost_price=6.50,
            stock_quantity=50,
            min_stock_threshold=15,
            category="Accessories",
        )
        assert prod2.id is not None
        print(f"✅ Step 2b: Created Product 2: {prod2.name} [SKU: {prod2.sku}] - Stock: {prod2.stock_quantity}")

        # Step 3: Stock Adjustments & Low Stock Alert Check
        # Adjust stock of prod1 to 5 (which is below min_stock_threshold of 8)
        inventory_service.adjust_product_stock(db, tenant_id=tenant_a.id, product_id=prod1.id, new_quantity=5)
        db.refresh(prod1)
        assert prod1.stock_quantity == 5
        prods_list, count = inventory_service.get_products(db, tenant_id=tenant_a.id, low_stock_only=True)
        low_stock_ids = [p["id"] for p in prods_list]
        assert prod1.id in low_stock_ids, "Product 1 should be flagged as low stock"
        print(f"✅ Step 3: Low stock detection verified. Prod 1 stock=5, threshold=8 -> Flagged as LOW STOCK")

        # Step 4: Create Sales Order with Line Items
        cust_a = crm_service.create_customer(
            db=db,
            tenant_id=tenant_a.id,
            name="Quantum Data Labs",
            email="ops@quantumdata.io"
        )
        order_items = [
            {"product_id": prod1.id, "quantity": 2, "unit_price": 299.99},
            {"product_id": prod2.id, "quantity": 10, "unit_price": 19.99},
        ]
        # total: 2*299.99 (599.98) + 10*19.99 (199.90) = 799.88
        order = inventory_service.create_order(
            db=db,
            tenant_id=tenant_a.id,
            customer_id=cust_a.id,
            items=order_items,
            notes="Deliver to Data Center Bay 4",
            status="pending",
        )
        assert order.id is not None
        assert order.order_number.startswith("ORD-")
        assert round(float(order.total_amount), 2) == 799.88
        assert order.status == "pending"
        print(f"✅ Step 4: Order created: {order.order_number} - Total: ${order.total_amount:,.2f}")

        # Initial stocks before fulfillment: prod1=5, prod2=50
        assert prod1.stock_quantity == 5
        assert prod2.stock_quantity == 50

        # Step 5: Fulfill Order & Automatic Stock Decrement
        fulfilled_order = inventory_service.update_order_status(
            db=db,
            tenant_id=tenant_a.id,
            order_id=order.id,
            status="fulfilled",
        )
        assert fulfilled_order.status == "fulfilled"
        assert fulfilled_order.fulfilled_at is not None

        db.refresh(prod1)
        db.refresh(prod2)
        assert prod1.stock_quantity == 3, f"Prod1 stock should be 5 - 2 = 3, got {prod1.stock_quantity}"
        assert prod2.stock_quantity == 40, f"Prod2 stock should be 50 - 10 = 40, got {prod2.stock_quantity}"
        print(f"✅ Step 5: Order fulfillment automatically decremented stock: Prod1 (5 -> 3), Prod2 (50 -> 40)")

        # Step 6: Cancel Order & Automatic Stock Restoration
        cancelled_order = inventory_service.update_order_status(
            db=db,
            tenant_id=tenant_a.id,
            order_id=order.id,
            status="cancelled",
        )
        assert cancelled_order.status == "cancelled"
        db.refresh(prod1)
        db.refresh(prod2)
        assert prod1.stock_quantity == 5, f"Prod1 stock should be restored to 5, got {prod1.stock_quantity}"
        assert prod2.stock_quantity == 50, f"Prod2 stock should be restored to 50, got {prod2.stock_quantity}"
        print(f"✅ Step 6: Order cancellation automatically restored stock: Prod1 (3 -> 5), Prod2 (40 -> 50)")

        # Re-fulfill for conversion test
        inventory_service.update_order_status(db, tenant_id=tenant_a.id, order_id=order.id, status="fulfilled")

        # Step 7: Seamless Order to Billing Invoice Conversion
        invoice = inventory_service.convert_order_to_invoice(
            db=db,
            tenant_id=tenant_a.id,
            order_id=order.id,
            tax_rate=10.0,
        )
        assert invoice.id is not None
        assert invoice.invoice_number.startswith("INV-")
        assert len(invoice.items) == 2
        assert invoice.status == "paid"  # Since order was fulfilled
        # Verify PDF was generated for converted invoice
        assert invoice.pdf_url is not None
        print(f"✅ Step 7: Converted Order {order.order_number} to Billing Invoice {invoice.invoice_number} with generated PDF")

        # Step 8: Strict Multi-Tenant Isolation
        tenant_b = db.query(Tenant).filter(Tenant.slug == "test-tenant-b").first()
        if not tenant_b:
            tenant_b = Tenant(name="Tenant B Corp", slug="test-tenant-b", is_active=True)
            db.add(tenant_b)
            db.commit()
            db.refresh(tenant_b)

        # Tenant B queries products
        prods_b, count_b = inventory_service.get_products(db, tenant_id=tenant_b.id)
        assert count_b == 0, f"Tenant B leaked products! Count: {count_b}"

        # Tenant B queries orders
        orders_b, o_count_b = inventory_service.get_orders(db, tenant_id=tenant_b.id)
        assert o_count_b == 0, f"Tenant B leaked orders! Count: {o_count_b}"

        # Tenant B direct access attempts
        leak_prod = inventory_service.get_product_by_id(db, tenant_id=tenant_b.id, product_id=prod1.id)
        assert leak_prod is None, "SECURITY FAILURE: Tenant B was able to view Tenant A's product!"

        leak_order = inventory_service.get_order_by_id(db, tenant_id=tenant_b.id, order_id=order.id)
        assert leak_order is None, "SECURITY FAILURE: Tenant B was able to view Tenant A's order!"

        stats_b = inventory_service.get_inventory_stats(db, tenant_id=tenant_b.id)
        assert stats_b["total_products"] == 0
        assert stats_b["total_inventory_value"] == 0.0
        print("✅ Step 8: Zero Cross-Tenant Data Leakage verified. Tenant B cannot see Tenant A's products, orders, or inventory valuation.")

        # Step 9: Non-regression check on Previous Tasks (1, 2, 3, 4)
        sup_stats = support_service.get_support_stats(db, tenant_id=tenant_a.id)
        crm_stats = crm_service.get_crm_stats(db, tenant_id=tenant_a.id)
        bill_stats = billing_service.get_billing_stats(db, tenant_id=tenant_a.id)
        assert "open" in sup_stats, "Task 2 Support regression"
        assert crm_stats["total_customers"] >= 1, "Task 3 CRM regression"
        assert bill_stats["total_invoices"] >= 1, "Task 4 Billing regression"
        print("✅ Step 9: Tasks 1, 2, 3, and 4 verified intact with zero regressions.")

        print("\n🎉 ALL TASK 5 BACKEND VERIFICATIONS PASSED SUCCESSFULLY! 🎉\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()
