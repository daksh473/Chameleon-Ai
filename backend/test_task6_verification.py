"""
TASK 6 Verification Script
Verifies:
1. Team user assignment and retrieval.
2. Task CRUD with priority, due dates, and polymorphic linkages (Lead, Ticket, Order, Customer).
3. Kanban board grouping (todo, in_progress, review, done).
4. Task status transitions and completion rate metrics.
5. Strict Multi-Tenant Isolation (Tenant B cannot see Tenant A's tasks, cannot link to Tenant A's entities).
6. Non-regression of Tasks 1, 2, 3, 4, 5 (Models, Support, CRM, Billing, Inventory).
"""
import sys
import os
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db.session import SessionLocal
from db.models import Tenant, Customer, Task, User
from core.tenancy import get_or_create_default_tenant
from services import task_service, crm_service, support_service, billing_service, inventory_service

def main():
    print("=== STARTING TASK 6 VERIFICATION ===")
    db = SessionLocal()

    try:
        # Step 1: Default Tenant (Tenant A)
        tenant_a = get_or_create_default_tenant(db)
        print(f"✅ Step 1: Default Tenant A: {tenant_a.name} ({tenant_a.id})")

        # Step 2: Ensure User exists for assignment
        user_a = task_service.get_or_create_default_user(db, tenant_a.id)
        assert user_a.id is not None
        users_list = task_service.get_tenant_users(db, tenant_a.id)
        assert len(users_list) >= 1
        print(f"✅ Step 2: Team Member ready for assignment: {user_a.full_name} ({user_a.email})")

        # Step 3: Create linked entities in Tenant A (CRM Customer, Lead, Support Ticket, Order)
        cust_a = crm_service.create_customer(
            db=db,
            tenant_id=tenant_a.id,
            name="Starlight Dynamics",
            email="contact@starlight.io"
        )
        lead_a = crm_service.create_lead(
            db=db,
            tenant_id=tenant_a.id,
            name="Starlight Dynamics",
            title="Q4 Cloud Expansion Deal",
            company="Starlight Dynamics",
            estimated_value=12000.0,
        )
        ticket_a = support_service.create_support_ticket(
            db=db,
            tenant_id=tenant_a.id,
            customer_name="Starlight Dynamics",
            customer_email="contact@starlight.io",
            issue="Urgent Gateway Timeout Issue",
        )
        prod_a = inventory_service.create_product(
            db=db,
            tenant_id=tenant_a.id,
            name="Quantum Server Rack",
            unit_price=1200.0,
            stock_quantity=5,
        )
        order_a = inventory_service.create_order(
            db=db,
            tenant_id=tenant_a.id,
            customer_id=cust_a.id,
            items=[{"product_id": prod_a.id, "quantity": 1, "unit_price": 1200.0}],
        )
        print("✅ Step 3: Created linked entities (Customer, Lead, Ticket, Order) in Tenant A")

        # Step 4: Create Tasks with Polymorphic Linkages
        task1 = task_service.create_task(
            db=db,
            tenant_id=tenant_a.id,
            title="Investigate Gateway Timeout",
            description="Diagnose latency spikes in API gateway",
            status="todo",
            priority="urgent",
            due_date=datetime.now(timezone.utc) + timedelta(hours=4),
            assigned_to_user_id=user_a.id,
            ticket_id=ticket_a.id,
        )
        assert task1.id is not None
        assert task1.ticket_id == ticket_a.id

        task2 = task_service.create_task(
            db=db,
            tenant_id=tenant_a.id,
            title="Prepare Starlight Cloud Proposal",
            description="Draft SLA contract terms for $12k deal",
            status="in_progress",
            priority="high",
            due_date=datetime.now(timezone.utc) + timedelta(days=2),
            assigned_to_user_id=user_a.id,
            lead_id=lead_a.id,
        )
        assert task2.id is not None

        task3 = task_service.create_task(
            db=db,
            tenant_id=tenant_a.id,
            title="Coordinate Rack Delivery",
            description="Arrange courier delivery for Order #" + order_a.order_number,
            status="review",
            priority="medium",
            due_date=datetime.now(timezone.utc) + timedelta(days=3),
            order_id=order_a.id,
        )
        assert task3.id is not None

        # Overdue task test
        task_overdue = task_service.create_task(
            db=db,
            tenant_id=tenant_a.id,
            title="Overdue Contract Review",
            status="todo",
            priority="high",
            due_date=datetime.now(timezone.utc) - timedelta(days=1),
            customer_id=cust_a.id,
        )
        print(f"✅ Step 4: Created 4 tasks with diverse polymorphic linkages & priorities")

        # Step 5: Kanban Board Grouping
        kanban = task_service.get_task_kanban(db, tenant_a.id)
        assert "todo" in kanban
        assert "in_progress" in kanban
        assert "review" in kanban
        assert "done" in kanban
        todo_ids = [t["id"] for t in kanban["todo"]]
        assert task1.id in todo_ids
        assert task_overdue.id in todo_ids
        in_prog_ids = [t["id"] for t in kanban["in_progress"]]
        assert task2.id in in_prog_ids
        print(f"✅ Step 5: Kanban board verified. Columns populated: todo={len(kanban['todo'])}, in_progress={len(kanban['in_progress'])}, review={len(kanban['review'])}, done={len(kanban['done'])}")

        # Step 6: Task Status Transitions & Stats
        task_service.update_task_status(db, tenant_a.id, task1.id, "done")
        task1_detail = task_service.get_task_by_id(db, tenant_a.id, task1.id)
        assert task1_detail["status"] == "done"

        stats_a = task_service.get_task_stats(db, tenant_a.id)
        assert stats_a["done"] >= 1
        assert stats_a["overdue"] >= 1
        assert stats_a["completion_rate"] > 0
        print(f"✅ Step 6: Status update to 'done' verified. Completion rate: {stats_a['completion_rate']}%")

        # Step 7: Strict Multi-Tenant Isolation
        tenant_b = db.query(Tenant).filter(Tenant.slug == "test-tenant-b").first()
        if not tenant_b:
            tenant_b = Tenant(name="Tenant B Corp", slug="test-tenant-b", is_active=True)
            db.add(tenant_b)
            db.commit()
            db.refresh(tenant_b)

        # Tenant B queries tasks
        tasks_b, count_b = task_service.get_tasks(db, tenant_b.id)
        assert count_b == 0, f"Tenant B leaked tasks! Count: {count_b}"

        # Tenant B queries kanban
        kanban_b = task_service.get_task_kanban(db, tenant_b.id)
        assert len(kanban_b["todo"]) == 0
        assert len(kanban_b["done"]) == 0

        # Tenant B direct access
        leak_task = task_service.get_task_by_id(db, tenant_b.id, task1.id)
        assert leak_task is None, "SECURITY FAILURE: Tenant B was able to view Tenant A's task!"

        # Tenant B cross-tenant linkage attempt (try linking to Tenant A's lead)
        try:
            task_service.create_task(
                db=db,
                tenant_id=tenant_b.id,
                title="Malicious Cross-Tenant Task",
                lead_id=lead_a.id
            )
            assert False, "SECURITY FAILURE: Tenant B was able to link to Tenant A's lead!"
        except ValueError as e:
            print("✅ Step 7: Blocked cross-tenant foreign entity linkage attempt cleanly:", e)

        print("✅ Step 7b: Zero Cross-Tenant Data Leakage verified. Tenant B cannot see or manipulate Tenant A's tasks.")

        # Step 8: Non-regression check on Previous Tasks (1, 2, 3, 4, 5)
        sup = support_service.get_support_stats(db, tenant_a.id)
        crm = crm_service.get_crm_stats(db, tenant_a.id)
        bil = billing_service.get_billing_stats(db, tenant_a.id)
        inv = inventory_service.get_inventory_stats(db, tenant_a.id)
        assert "open" in sup, "Task 2 Support regression"
        assert crm["total_customers"] >= 1, "Task 3 CRM regression"
        assert bil["total_invoices"] >= 1, "Task 4 Billing regression"
        assert inv["total_products"] >= 1, "Task 5 Inventory regression"
        print("✅ Step 8: Tasks 1, 2, 3, 4, and 5 verified intact with zero regressions.")

        print("\n🎉 ALL TASK 6 BACKEND VERIFICATIONS PASSED SUCCESSFULLY! 🎉\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()
