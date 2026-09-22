import json
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import (
    AnalyticsSnapshot, Ticket, Invoice, Lead, Order, Product, Task, Customer
)
from services import (
    crm_service, support_service, billing_service, inventory_service, task_service
)


# ==============================================================================
# DAILY SNAPSHOT ENGINE
# ==============================================================================

def capture_daily_snapshot(
    db: Session,
    tenant_id: str,
    target_date: Optional[date] = None,
) -> AnalyticsSnapshot:
    """
    Computes and records or updates today's AnalyticsSnapshot strictly scoped to tenant_id.
    Zero cross-tenant leakage.
    """
    snap_date = target_date or date.today()

    # 1. Support
    open_tickets = db.query(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        Ticket.status.in_(["OPEN", "IN_PROGRESS", "ESCALATED"])
    ).count()

    # 2. Billing (Revenue this month)
    first_of_month = snap_date.replace(day=1)
    revenue_this_month = db.query(func.sum(Invoice.total_amount)).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.status == "paid",
        Invoice.issue_date >= first_of_month,
        Invoice.issue_date <= snap_date,
    ).scalar() or 0.0

    # 3. CRM (New leads this week)
    seven_days_ago = snap_date - timedelta(days=7)
    new_leads_this_week = db.query(Lead).filter(
        Lead.tenant_id == tenant_id,
        func.date(Lead.created_at) >= seven_days_ago,
        func.date(Lead.created_at) <= snap_date,
    ).count()

    # 4. Inventory (Pending orders)
    pending_orders = db.query(Order).filter(
        Order.tenant_id == tenant_id,
        Order.status.in_(["pending", "processing"])
    ).count()

    # 5. Overdue Invoices
    overdue_invoices = db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.status == "overdue"
    ).count()

    # 6. Tasks (Completion rate)
    total_tasks = db.query(Task).filter(Task.tenant_id == tenant_id).count()
    done_tasks = db.query(Task).filter(Task.tenant_id == tenant_id, Task.status == "done").count()
    task_rate = round((done_tasks / total_tasks * 100.0), 1) if total_tasks > 0 else 0.0

    # 7. Extended Telemetry JSON
    telemetry = {
        "total_customers": db.query(Customer).filter(Customer.tenant_id == tenant_id).count(),
        "total_products": db.query(Product).filter(Product.tenant_id == tenant_id, Product.is_active == True).count(),
        "total_revenue_lifetime": float(db.query(func.sum(Invoice.total_amount)).filter(
            Invoice.tenant_id == tenant_id, Invoice.status == "paid"
        ).scalar() or 0.0),
    }

    # Check if snapshot for this date and tenant already exists
    snapshot = db.query(AnalyticsSnapshot).filter(
        AnalyticsSnapshot.tenant_id == tenant_id,
        AnalyticsSnapshot.snapshot_date == snap_date
    ).first()

    if not snapshot:
        snapshot = AnalyticsSnapshot(
            tenant_id=tenant_id,
            snapshot_date=snap_date,
            open_tickets=open_tickets,
            revenue_this_month=round(float(revenue_this_month), 2),
            new_leads_this_week=new_leads_this_week,
            pending_orders=pending_orders,
            overdue_invoices=overdue_invoices,
            task_completion_rate=task_rate,
            metrics_json=json.dumps(telemetry),
        )
        db.add(snapshot)
    else:
        snapshot.open_tickets = open_tickets
        snapshot.revenue_this_month = round(float(revenue_this_month), 2)
        snapshot.new_leads_this_week = new_leads_this_week
        snapshot.pending_orders = pending_orders
        snapshot.overdue_invoices = overdue_invoices
        snapshot.task_completion_rate = task_rate
        snapshot.metrics_json = json.dumps(telemetry)

    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_historical_snapshots(
    db: Session,
    tenant_id: str,
    days: int = 14,
) -> List[Dict[str, Any]]:
    """
    Get daily snapshot timeline for charting trends over time.
    Strictly isolated by tenant_id.
    """
    # Always ensure today's snapshot is present
    capture_daily_snapshot(db, tenant_id)

    start_date = date.today() - timedelta(days=days)
    snapshots = db.query(AnalyticsSnapshot).filter(
        AnalyticsSnapshot.tenant_id == tenant_id,
        AnalyticsSnapshot.snapshot_date >= start_date
    ).order_by(AnalyticsSnapshot.snapshot_date.asc()).all()

    results = []
    for s in snapshots:
        results.append({
            "id": s.id,
            "date": str(s.snapshot_date),
            "open_tickets": s.open_tickets,
            "revenue": float(s.revenue_this_month),
            "new_leads": s.new_leads_this_week,
            "pending_orders": s.pending_orders,
            "overdue_invoices": s.overdue_invoices,
            "task_completion_rate": s.task_completion_rate,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return results


# ==============================================================================
# UNIFIED EXECUTIVE DASHBOARD
# ==============================================================================

def get_executive_bms_dashboard(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Unified multi-module executive overview combining CRM, Support, Billing,
    Inventory, Tasks, and an intelligent Business Health Score.
    Strictly isolated by tenant_id.
    """
    # Gather live module metrics
    crm_stats = crm_service.get_crm_stats(db, tenant_id=tenant_id)
    support_stats = support_service.get_support_stats(db, tenant_id=tenant_id)
    billing_stats = billing_service.get_billing_stats(db, tenant_id=tenant_id)
    inventory_stats = inventory_service.get_inventory_stats(db, tenant_id=tenant_id)
    task_stats = task_service.get_task_stats(db, tenant_id=tenant_id)

    # Compute Unified Business Health Score (0 - 100)
    score = 70.0  # Baseline

    # Support sentiment adjustment (+15 to -15)
    avg_sent = float(support_stats.get("average_sentiment", 0.5))
    score += (avg_sent - 0.5) * 30.0

    # Overdue tickets penalty
    open_tickets = int(support_stats.get("open", 0))
    if open_tickets > 5:
        score -= min(15.0, (open_tickets - 5) * 2.0)

    # Billing overdue penalty
    overdue_invs = int(billing_stats.get("overdue_invoices", 0))
    if overdue_invs > 0:
        score -= min(15.0, overdue_invs * 5.0)

    # Task completion reward (+10)
    comp_rate = float(task_stats.get("completion_rate", 0.0))
    if comp_rate >= 50.0:
        score += 8.0
    elif comp_rate < 20.0 and task_stats.get("total", 0) > 3:
        score -= 5.0

    # Inventory low stock warning
    low_stock = int(inventory_stats.get("low_stock_items", 0))
    if low_stock > 2:
        score -= 5.0

    final_score = int(max(10, min(100, round(score))))
    trend = "improving" if final_score >= 75 else "declining" if final_score < 50 else "stable"

    # Business Insights
    insights = []
    if billing_stats.get("total_revenue", 0) > 0:
        insights.append(f"Revenue is healthy at ${billing_stats['total_revenue']:,.2f} with {billing_stats['paid_invoices']} paid invoice(s).")
    else:
        insights.append("No collected revenue recorded yet. Review open proposals and pending invoices.")

    if overdue_invs > 0:
        insights.append(f"Action required: {overdue_invs} invoice(s) are overdue totaling ${billing_stats.get('overdue_amount', 0):,.2f}.")
    else:
        insights.append("Invoice receivables are up-to-date with 0 overdue accounts.")

    if low_stock > 0:
        insights.append(f"Supply chain alert: {low_stock} product(s) are running below safety reorder thresholds.")
    else:
        insights.append("Inventory levels across all catalog items are sufficient.")

    return {
        "health_score": final_score,
        "health_trend": trend,
        "insights": insights,
        "modules": {
            "crm": crm_stats,
            "support": support_stats,
            "billing": billing_stats,
            "inventory": inventory_stats,
            "tasks": task_stats,
        },
        "summary": {
            "total_revenue": billing_stats.get("total_revenue", 0.0),
            "pipeline_value": crm_stats.get("pipeline_deal_value", 0.0),
            "open_tickets": open_tickets,
            "active_products": inventory_stats.get("total_products", 0),
            "inventory_valuation": inventory_stats.get("total_inventory_value", 0.0),
            "task_completion_rate": comp_rate,
        }
    }
