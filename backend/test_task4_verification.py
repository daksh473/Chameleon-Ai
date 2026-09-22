"""
TASK 4 Verification Script
Verifies:
1. Invoice CRUD with line items (auto-calculation of subtotal, tax, discount, total).
2. ReportLab PDF generation and file verification.
3. Status tracking and transition (pending -> paid -> customer revenue sync).
4. APScheduler overdue invoice detection and update.
5. Strict Multi-Tenant Isolation (Tenant B cannot access or leak Tenant A's invoices).
6. Non-regression of Task 1, 2, 3 (CRM, Support, Models).
"""
import sys
import os
from datetime import date, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db.session import SessionLocal
from db.models import Tenant, Customer, Invoice, InvoiceItem
from core.tenancy import get_or_create_default_tenant
from services import billing_service, crm_service
from services.billing_scheduler import run_billing_check_now

def main():
    print("=== STARTING TASK 4 VERIFICATION ===")
    db = SessionLocal()

    try:
        # Step 1: Default Tenant (Tenant A)
        tenant_a = get_or_create_default_tenant(db)
        print(f"✅ Step 1: Default Tenant A: {tenant_a.name} ({tenant_a.id})")

        # Step 2: Create a CRM customer in Tenant A
        customer_a = crm_service.create_customer(
            db=db,
            tenant_id=tenant_a.id,
            name="Apex Tech Industries",
            email="billing@apextech.io",
            company="Apex Tech",
        )
        print(f"✅ Step 2: Created Customer in Tenant A: {customer_a.name} ({customer_a.id})")

        # Step 3: Create an Invoice with Line Items
        items = [
            {"description": "Enterprise Cloud License - Q3", "quantity": 2, "unit_price": 750.00},
            {"description": "AI Copilot Onboarding Package", "quantity": 1, "unit_price": 500.00},
            {"description": "Dedicated Support SLA", "quantity": 1, "unit_price": 250.00},
        ]
        # subtotal: 2*750 (1500) + 500 + 250 = 2250.00
        # tax (10%): 225.00
        # discount: 50.00
        # total: 2425.00
        invoice_a = billing_service.create_invoice(
            db=db,
            tenant_id=tenant_a.id,
            customer_id=customer_a.id,
            items=items,
            tax_rate=10.0,
            discount_amount=50.0,
            notes="Net 30 days. Thank you for choosing Chameleon BMS.",
            status="pending",
            auto_generate_pdf=True,
        )

        assert invoice_a.id is not None, "Invoice ID must not be None"
        assert invoice_a.invoice_number.startswith("INV-"), f"Unexpected invoice number format: {invoice_a.invoice_number}"
        assert float(invoice_a.subtotal) == 2250.00, f"Subtotal mismatch: {invoice_a.subtotal}"
        assert float(invoice_a.tax_amount) == 225.00, f"Tax mismatch: {invoice_a.tax_amount}"
        assert float(invoice_a.discount_amount) == 50.00, f"Discount mismatch: {invoice_a.discount_amount}"
        assert float(invoice_a.total_amount) == 2425.00, f"Total mismatch: {invoice_a.total_amount}"
        assert len(invoice_a.items) == 3, f"Expected 3 items, got {len(invoice_a.items)}"
        print(f"✅ Step 3: Created Invoice {invoice_a.invoice_number} - Total: ${invoice_a.total_amount:,.2f}")

        # Step 4: Verify PDF Generation
        pdf_path = billing_service.get_invoice_pdf_path(db, tenant_id=tenant_a.id, invoice_id=invoice_a.id)
        assert pdf_path and os.path.exists(pdf_path), f"PDF file does not exist at {pdf_path}"
        with open(pdf_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-", f"Invalid PDF header: {header}"
        file_size = os.path.getsize(pdf_path)
        assert file_size > 500, f"PDF file too small ({file_size} bytes)"
        print(f"✅ Step 4: PDF verified at {pdf_path} ({file_size} bytes, starts with %PDF-)")

        # Step 5: Test Status Update & Customer Revenue Sync
        assert float(customer_a.revenue_generated or 0.0) == 0.0, "Customer initial revenue should be 0.0"
        updated_inv = billing_service.update_invoice_status(
            db=db,
            tenant_id=tenant_a.id,
            invoice_id=invoice_a.id,
            status="paid"
        )
        assert updated_inv.status == "paid"
        assert updated_inv.paid_at is not None
        db.refresh(customer_a)
        assert float(customer_a.revenue_generated) == 2425.00, f"Customer revenue not synced! Found: {customer_a.revenue_generated}"
        print(f"✅ Step 5: Invoice marked 'paid' and customer revenue synced to ${customer_a.revenue_generated:,.2f}")

        # Step 6: Test APScheduler Overdue Scanner
        past_due_date = date.today() - timedelta(days=5)
        invoice_overdue_test = billing_service.create_invoice(
            db=db,
            tenant_id=tenant_a.id,
            items=[{"description": "Past Due Consultation", "quantity": 1, "unit_price": 300.0}],
            due_date=past_due_date,
            status="pending",
            auto_generate_pdf=False,
        )
        assert invoice_overdue_test.status == "pending"

        # Trigger scheduler job
        overdue_res = run_billing_check_now(tenant_id=tenant_a.id)
        overdue_ids = [o["id"] for o in overdue_res]
        assert invoice_overdue_test.id in overdue_ids, f"Expected invoice {invoice_overdue_test.id} in overdue list: {overdue_ids}"

        db.refresh(invoice_overdue_test)
        assert invoice_overdue_test.status == "overdue"
        assert invoice_overdue_test.last_reminder_sent_at is not None
        print(f"✅ Step 6: APScheduler overdue scan marked {invoice_overdue_test.invoice_number} as 'overdue'")

        # Step 7: STRICT MULTI-TENANT ISOLATION
        tenant_b = db.query(Tenant).filter(Tenant.slug == "test-tenant-b").first()
        if not tenant_b:
            tenant_b = Tenant(name="Tenant B Corp", slug="test-tenant-b", is_active=True)
            db.add(tenant_b)
            db.commit()
            db.refresh(tenant_b)
        print(f"✅ Step 7a: Created/Loaded Tenant B: {tenant_b.name} ({tenant_b.id})")

        # Tenant B queries invoices
        invs_b, count_b = billing_service.get_invoices(db, tenant_id=tenant_b.id)
        assert count_b == 0, f"Tenant B leaked invoices! Count: {count_b}"

        # Tenant B attempts to fetch Tenant A's invoice directly
        leak_check = billing_service.get_invoice_by_id(db, tenant_id=tenant_b.id, invoice_id=invoice_a.id)
        assert leak_check is None, "SECURITY FAILURE: Tenant B was able to view Tenant A's invoice!"

        # Tenant B attempts to fetch Tenant A's PDF
        leak_pdf = billing_service.get_invoice_pdf_path(db, tenant_id=tenant_b.id, invoice_id=invoice_a.id)
        assert leak_pdf is None, "SECURITY FAILURE: Tenant B was able to access Tenant A's invoice PDF!"

        # Tenant B stats
        stats_b = billing_service.get_billing_stats(db, tenant_id=tenant_b.id)
        assert stats_b["total_invoices"] == 0
        assert stats_b["total_revenue"] == 0.0
        print("✅ Step 7b: Zero Cross-Tenant Data Leakage verified. Tenant B cannot see Tenant A's invoices, PDFs, or revenue.")

        # Step 8: Non-regression check on CRM and Support
        from services.support_service import get_support_stats
        crm_stats = crm_service.get_crm_stats(db, tenant_id=tenant_a.id)
        support_stats = get_support_stats(db, tenant_id=tenant_a.id)
        assert crm_stats["total_customers"] >= 1, "CRM stats regression"
        assert "open" in support_stats, "Support stats regression"
        print("✅ Step 8: CRM & Support modules remain healthy with zero regressions.")

        print("\n🎉 ALL TASK 4 BACKEND VERIFICATIONS PASSED SUCCESSFULLY! 🎉\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()
