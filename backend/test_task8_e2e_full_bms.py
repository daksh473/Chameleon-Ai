"""
TASK 8 — Full End-to-End BMS System Integration & Multi-Tenant Verification
Validates:
1. Organization Provisioning: Independent workspaces for Tenant Alpha & Tenant Beta.
2. Full Customer Lifecycle in Tenant Alpha:
   Lead -> Customer -> Support Ticket & Caspian triage -> Product & Sales Order ->
   Fulfillment (stock decremented) -> Converted to Invoice -> Paid (revenue incremented) ->
   Team Task Assignment & Completion -> Daily Analytics Snapshot & Executive BMS Dashboard.
3. Strict Multi-Tenant Isolation:
   Zero data leakage from Tenant Alpha to Tenant Beta across all 6 core modules
   (CRM, Support, Inventory, Billing, Tasks, Analytics).
4. FastAPI HTTP Layer Verification:
   Ensures X-Tenant-ID header correctly switches context across API endpoints.
"""
import sys
import os
import uuid
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from db.session import SessionLocal
from db.models import Tenant, Lead, Customer, Product, Order, Invoice, Task, Ticket
from main import app
from services import (
    crm_service, support_service, billing_service,
    inventory_service, task_service, analytics_service
)


def run_e2e_test():
    print("=================================================================")
    print("  TASK 8: END-TO-END BMS SYSTEM INTEGRATION & TENANCY TEST")
    print("=================================================================")

    client = TestClient(app)
    db = SessionLocal()

    try:
        # ─────────────────────────────────────────────────────────────
        # STEP 1: Provision Two Distinct Organizations via HTTP API
        # ─────────────────────────────────────────────────────────────
        print("\n--- STEP 1: Provisioning Organizations ---")
        suffix = uuid.uuid4().hex[:6]
        alpha_name = f"Alpha Global Tech {suffix}"
        beta_name = f"Beta Logistics {suffix}"

        res_alpha = client.post("/tenants", json={"name": alpha_name})
        assert res_alpha.status_code == 201, f"Failed to create Tenant Alpha: {res_alpha.text}"
        tenant_alpha = res_alpha.json()
        alpha_id = tenant_alpha["id"]
        print(f"✅ Provisioned Tenant Alpha: '{alpha_name}' (ID: {alpha_id})")

        res_beta = client.post("/tenants", json={"name": beta_name})
        assert res_beta.status_code == 201, f"Failed to create Tenant Beta: {res_beta.text}"
        tenant_beta = res_beta.json()
        beta_id = tenant_beta["id"]
        print(f"✅ Provisioned Tenant Beta: '{beta_name}' (ID: {beta_id})")

        # Verify /tenants endpoint lists both
        res_list = client.get("/tenants")
        assert res_list.status_code == 200
        tenant_ids = [t["id"] for t in res_list.json()]
        assert alpha_id in tenant_ids
        assert beta_id in tenant_ids
        print("✅ /tenants endpoint lists both organizations correctly.")

        # ─────────────────────────────────────────────────────────────
        # STEP 2: Full Customer Journey in Tenant Alpha
        # ─────────────────────────────────────────────────────────────
        print("\n--- STEP 2: Full Customer Journey in Tenant Alpha ---")

        # 2a. CRM: Create a Lead
        lead = crm_service.create_lead(
            db=db,
            tenant_id=alpha_id,
            name="Marcus Vance",
            company="Vance Enterprises",
            email=f"marcus.{suffix}@alphaclient.com",
            phone="+1-555-0199",
            status="qualified",
            estimated_value=25000.0,
            notes="Interested in full cloud deployment suite"
        )
        print(f"✅ 2a. Created Lead: '{lead.name}' at '{lead.company}' (${float(lead.estimated_value):,.2f})")

        # 2b. CRM: Convert Lead to Customer
        customer = crm_service.convert_lead_to_customer(
            db=db,
            tenant_id=alpha_id,
            lead_id=lead.id
        )
        assert customer is not None
        assert customer.id is not None
        assert customer.company == "Vance Enterprises"
        print(f"✅ 2b. Converted to Customer: '{customer.name}' at '{customer.company}'")

        # 2c. Support: Create Ticket & Caspian Analysis
        ticket = support_service.create_support_ticket(
            db=db,
            tenant_id=alpha_id,
            customer_name=customer.name,
            customer_email=customer.email,
            issue="Pre-deployment environment validation and security check",
            score=0.92,
            channel="web_chat"
        )
        # Add a Caspian conversation message
        msg = support_service.save_support_conversation_message(
            db=db,
            tenant_id=alpha_id,
            session_id=f"sess-{suffix}",
            role="user",
            message="We need this environment configured by Thursday. Looking forward to going live!",
            score=0.92,
            emotion="grateful",
            action="NORMAL"
        )
        print(f"✅ 2c. Created Support Ticket #{ticket.ticket_number} with Caspian triage (Score: {ticket.sentiment_score}, Emotion: {ticket.emotion})")

        # 2d. Inventory: Catalog Setup
        product = inventory_service.create_product(
            db=db,
            tenant_id=alpha_id,
            name="Alpha Cloud Server Rack",
            category="Hardware",
            unit_price=1200.00,
            cost_price=750.00,
            stock_quantity=50,
            min_stock_threshold=5
        )
        print(f"✅ 2d. Created Product: '{product.name}' (SKU: {product.sku}, Stock: {product.stock_quantity})")

        # 2e. Inventory: Create Sales Order
        order = inventory_service.create_order(
            db=db,
            tenant_id=alpha_id,
            customer_id=customer.id,
            items=[
                {
                    "product_id": product.id,
                    "quantity": 5,
                    "unit_price": 1200.00,
                }
            ],
            notes="Expedited delivery for Marcus Vance"
        )
        assert order.status == "pending"
        assert float(order.total_amount) == 6000.00
        print(f"✅ 2e. Created Sales Order #{order.order_number}: Total=${float(order.total_amount):,.2f}")

        # 2f. Inventory: Fulfill Order & Verify Stock Decrement
        fulfilled_order = inventory_service.update_order_status(
            db=db,
            tenant_id=alpha_id,
            order_id=order.id,
            status="fulfilled"
        )
        assert fulfilled_order.status == "fulfilled"
        db.refresh(product)
        assert product.stock_quantity == 45, f"Expected 45, got {product.stock_quantity}"
        print(f"✅ 2f. Order Fulfilled: Stock decremented automatically from 50 -> {product.stock_quantity}")

        # 2g. Billing: Convert Sales Order to Invoice
        invoice = inventory_service.convert_order_to_invoice(
            db=db,
            tenant_id=alpha_id,
            order_id=order.id
        )
        assert invoice.status == "paid"
        print(f"✅ 2g. Converted Fulfilled Order to Invoice #{invoice.invoice_number} (Status: {invoice.status}, Total: ${float(invoice.total_amount):,.2f})")

        # 2h. Billing: Verify Customer revenue is synchronized
        db.refresh(customer)
        assert float(customer.revenue_generated) >= 6000.00, f"Expected >= 6000, got {customer.revenue_generated}"
        print(f"✅ 2h. Invoice Paid: Customer total revenue synchronized to ${float(customer.revenue_generated):,.2f}")

        # 2i. Tasks: Team Task Assignment
        task = task_service.create_task(
            db=db,
            tenant_id=alpha_id,
            title="Deploy Vance Cloud Rack Hardware",
            priority="high",
            status="in_progress",
            order_id=order.id,
            customer_id=customer.id
        )
        # Complete task
        completed_task = task_service.update_task(
            db=db,
            tenant_id=alpha_id,
            task_id=task.id,
            status="done"
        )
        assert completed_task.status == "done"
        print(f"✅ 2i. Team Task '{task.title}' linked to Order #{order.order_number} and moved to DONE.")

        # 2j. Analytics: Snapshot & Dashboard
        snapshot = analytics_service.capture_daily_snapshot(db=db, tenant_id=alpha_id)
        assert snapshot.snapshot_date == date.today()
        dashboard = analytics_service.get_executive_bms_dashboard(db=db, tenant_id=alpha_id)
        assert dashboard["health_score"] > 0
        assert dashboard["summary"]["total_revenue"] >= 6000.00
        print(f"✅ 2j. Analytics Snapshot & BMS Dashboard: Health Score={dashboard['health_score']}/100, Revenue=${dashboard['summary']['total_revenue']:,.2f}")

        # ─────────────────────────────────────────────────────────────
        # STEP 3: Strict Multi-Tenant Isolation Verification
        # ─────────────────────────────────────────────────────────────
        print("\n--- STEP 3: Verifying Strict Tenant Isolation (Tenant Beta) ---")

        # 3a. CRM Isolation
        beta_leads = crm_service.get_leads(db, tenant_id=beta_id)
        assert len(beta_leads) == 0, f"LEAKAGE: Beta sees {len(beta_leads)} leads from Alpha!"
        beta_customers = crm_service.get_customers(db, tenant_id=beta_id)
        assert len(beta_customers) == 0, f"LEAKAGE: Beta sees {len(beta_customers)} customers from Alpha!"
        print("✅ 3a. CRM: Tenant Beta sees 0 leads and 0 customers.")

        # 3b. Support Isolation
        beta_tickets = support_service.get_tenant_tickets(db, tenant_id=beta_id)
        assert len(beta_tickets) == 0, f"LEAKAGE: Beta sees {len(beta_tickets)} tickets from Alpha!"
        print("✅ 3b. Support: Tenant Beta sees 0 support tickets.")

        # 3c. Inventory Isolation
        beta_products, _ = inventory_service.get_products(db, tenant_id=beta_id)
        assert len(beta_products) == 0, f"LEAKAGE: Beta sees {len(beta_products)} products from Alpha!"
        beta_orders, _ = inventory_service.get_orders(db, tenant_id=beta_id)
        assert len(beta_orders) == 0, f"LEAKAGE: Beta sees {len(beta_orders)} sales orders from Alpha!"
        print("✅ 3c. Inventory: Tenant Beta sees 0 products and 0 sales orders.")

        # 3d. Billing Isolation
        beta_invoices, _ = billing_service.get_invoices(db, tenant_id=beta_id)
        assert len(beta_invoices) == 0, f"LEAKAGE: Beta sees {len(beta_invoices)} invoices from Alpha!"
        print("✅ 3d. Billing: Tenant Beta sees 0 invoices.")

        # 3e. Tasks Isolation
        beta_tasks, _ = task_service.get_tasks(db, tenant_id=beta_id)
        assert len(beta_tasks) == 0, f"LEAKAGE: Beta sees {len(beta_tasks)} tasks from Alpha!"
        print("✅ 3e. Tasks: Tenant Beta sees 0 team tasks.")

        # 3f. Analytics Isolation
        beta_dashboard = analytics_service.get_executive_bms_dashboard(db, tenant_id=beta_id)
        assert beta_dashboard["summary"]["total_revenue"] == 0.0, "LEAKAGE: Beta sees revenue from Alpha!"
        assert beta_dashboard["summary"]["open_tickets"] == 0
        assert beta_dashboard["summary"]["active_products"] == 0
        print("✅ 3f. Analytics: Tenant Beta shows clean slate ($0.00 revenue, 0 open tickets, 0 products).")

        # ─────────────────────────────────────────────────────────────
        # STEP 4: HTTP API Header Verification (X-Tenant-ID)
        # ─────────────────────────────────────────────────────────────
        print("\n--- STEP 4: Verifying HTTP API Header Injection (X-Tenant-ID) ---")

        # Tenant Alpha via HTTP
        res_crm_alpha = client.get("/crm/customers", headers={"X-Tenant-ID": alpha_id})
        assert res_crm_alpha.status_code == 200
        alpha_api_customers = res_crm_alpha.json()
        assert len(alpha_api_customers) >= 1
        assert alpha_api_customers[0]["name"] == "Marcus Vance"
        print(f"✅ HTTP API (Alpha Header): Successfully retrieved '{alpha_api_customers[0]['name']}'.")

        # Tenant Beta via HTTP with X-Tenant-ID
        res_crm_beta = client.get("/crm/customers", headers={"X-Tenant-ID": beta_id})
        assert res_crm_beta.status_code == 200
        beta_api_customers = res_crm_beta.json()
        assert len(beta_api_customers) == 0, "LEAKAGE via HTTP: Beta retrieved Alpha's customers!"
        print("✅ HTTP API (Beta Header): Successfully returned 0 customers (strict isolation confirmed).")

        # Verify cross-tenant access denial / 404 when querying Alpha's resource with Beta's header
        res_forbidden = client.get(f"/crm/customers/{customer.id}", headers={"X-Tenant-ID": beta_id})
        assert res_forbidden.status_code == 404
        print("✅ HTTP Cross-Tenant Protection: Accessing Alpha's customer ID with Beta's header correctly returns 404 Not Found.")

        print("\n=================================================================")
        print("  🎉 ALL TASK 8 VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
        print("=================================================================\n")

    finally:
        db.close()


if __name__ == "__main__":
    run_e2e_test()
