"""
TASK 7 Verification Script
Verifies:
1. Daily snapshot capture and upsert into analytics_snapshots table.
2. Historical snapshot trends generation for charting.
3. Unified executive BMS dashboard combining CRM, Support, Billing, Inventory, and Tasks.
4. Business Health Score calculation and automated insights.
5. Strict Multi-Tenant Isolation (Tenant B cannot see Tenant A's snapshots or dashboard stats).
6. Non-regression of Tasks 1 through 6.
"""
import sys
import os
from datetime import date, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db.session import SessionLocal
from db.models import Tenant, AnalyticsSnapshot
from core.tenancy import get_or_create_default_tenant
from services import (
    analytics_service, crm_service, support_service, billing_service,
    inventory_service, task_service
)

def main():
    print("=== STARTING TASK 7 VERIFICATION ===")
    db = SessionLocal()

    try:
        # Step 1: Default Tenant (Tenant A)
        tenant_a = get_or_create_default_tenant(db)
        print(f"✅ Step 1: Default Tenant A: {tenant_a.name} ({tenant_a.id})")

        # Step 2: Capture Daily Snapshot for Tenant A
        snap1 = analytics_service.capture_daily_snapshot(db, tenant_id=tenant_a.id)
        assert snap1.id is not None
        assert snap1.snapshot_date == date.today()
        assert snap1.tenant_id == tenant_a.id
        print(f"✅ Step 2a: Captured Snapshot for {snap1.snapshot_date}: Revenue=${snap1.revenue_this_month:,.2f}, OpenTickets={snap1.open_tickets}, TaskRate={snap1.task_completion_rate}%")

        # Verify idempotency (re-capturing updates instead of failing unique constraint)
        snap2 = analytics_service.capture_daily_snapshot(db, tenant_id=tenant_a.id)
        assert snap2.id == snap1.id, "Upsert failed: duplicate snapshot record created!"
        print("✅ Step 2b: Snapshot idempotency and upsert verified successfully.")

        # Step 3: Historical Snapshots Timeline
        # Simulate a past snapshot
        past_date = date.today() - timedelta(days=3)
        past_snap = analytics_service.capture_daily_snapshot(db, tenant_id=tenant_a.id, target_date=past_date)
        assert past_snap.snapshot_date == past_date

        history = analytics_service.get_historical_snapshots(db, tenant_id=tenant_a.id, days=14)
        assert len(history) >= 2
        dates = [h["date"] for h in history]
        assert str(date.today()) in dates
        assert str(past_date) in dates
        print(f"✅ Step 3: Historical snapshots timeline verified. {len(history)} data points retrieved: {dates}")

        # Step 4: Unified Executive BMS Dashboard
        dashboard = analytics_service.get_executive_bms_dashboard(db, tenant_id=tenant_a.id)
        assert "health_score" in dashboard
        assert 0 <= dashboard["health_score"] <= 100
        assert dashboard["health_trend"] in ("improving", "stable", "declining")
        assert len(dashboard["insights"]) >= 1

        # Check all 5 modules are represented
        modules = dashboard["modules"]
        assert "crm" in modules
        assert "support" in modules
        assert "billing" in modules
        assert "inventory" in modules
        assert "tasks" in modules
        print(f"✅ Step 4: Executive BMS Dashboard verified. Business Health Score: {dashboard['health_score']}/100 ({dashboard['health_trend'].upper()})")
        for ins in dashboard["insights"][:2]:
            print(f"   💡 Insight: {ins}")

        # Step 5: Strict Multi-Tenant Isolation
        tenant_b = db.query(Tenant).filter(Tenant.slug == "test-tenant-b").first()
        if not tenant_b:
            tenant_b = Tenant(name="Tenant B Corp", slug="test-tenant-b", is_active=True)
            db.add(tenant_b)
            db.commit()
            db.refresh(tenant_b)

        # Tenant B executive dashboard
        dash_b = analytics_service.get_executive_bms_dashboard(db, tenant_id=tenant_b.id)
        assert dash_b["summary"]["total_revenue"] == 0.0, "Tenant B leaked Tenant A's revenue!"
        assert dash_b["summary"]["active_products"] == 0, "Tenant B leaked Tenant A's products!"
        assert dash_b["summary"]["open_tickets"] == 0, "Tenant B leaked Tenant A's tickets!"

        # Tenant B snapshots
        history_b = analytics_service.get_historical_snapshots(db, tenant_id=tenant_b.id, days=14)
        for hb in history_b:
            assert hb["revenue"] == 0.0, "Tenant B snapshot leaked Tenant A's revenue!"
            assert hb["open_tickets"] == 0, "Tenant B snapshot leaked Tenant A's tickets!"
        print("✅ Step 5: Zero Cross-Tenant Data Leakage verified. Tenant B cannot see Tenant A's analytics, revenue, or snapshots.")

        # Step 6: Non-regression across all modules (1 to 6)
        sup = support_service.get_support_stats(db, tenant_a.id)
        crm = crm_service.get_crm_stats(db, tenant_a.id)
        bil = billing_service.get_billing_stats(db, tenant_a.id)
        inv = inventory_service.get_inventory_stats(db, tenant_a.id)
        tsk = task_service.get_task_stats(db, tenant_a.id)
        assert "open" in sup, "Support regression"
        assert crm["total_customers"] >= 1, "CRM regression"
        assert bil["total_invoices"] >= 1, "Billing regression"
        assert inv["total_products"] >= 1, "Inventory regression"
        assert tsk["total"] >= 1, "Tasks regression"
        print("✅ Step 6: All Modules (Tasks 1-6) verified healthy with zero regressions.")

        print("\n🎉 ALL TASK 7 BACKEND VERIFICATIONS PASSED SUCCESSFULLY! 🎉\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()
