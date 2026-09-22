import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db.session import SessionLocal
from services.billing_service import check_and_update_overdue_invoices

logger = logging.getLogger("billing_scheduler")
logger.setLevel(logging.INFO)

scheduler: Optional[BackgroundScheduler] = None


def scheduled_overdue_and_reminder_job():
    """
    Scheduled job executed periodically to scan for past-due invoices,
    mark them as 'overdue', and register reminder timestamps.
    """
    db = SessionLocal()
    try:
        updated = check_and_update_overdue_invoices(db)
        if updated:
            logger.info(f"[BillingScheduler] Processed {len(updated)} overdue invoices: {[u['invoice_number'] for u in updated]}")
        else:
            logger.debug("[BillingScheduler] Check completed: No new overdue invoices.")
    except Exception as e:
        logger.error(f"[BillingScheduler] Error executing invoice overdue check: {e}")
    finally:
        db.close()


def start_billing_scheduler(interval_hours: int = 1):
    """
    Start the APScheduler background scheduler for billing jobs.
    """
    global scheduler
    if scheduler is not None and scheduler.running:
        logger.info("[BillingScheduler] Scheduler already running.")
        return

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        scheduled_overdue_and_reminder_job,
        trigger=IntervalTrigger(hours=interval_hours),
        id="check_overdue_invoices_job",
        name="Scan and update overdue invoices",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"[BillingScheduler] Background scheduler started (running every {interval_hours} hour(s)).")


def stop_billing_scheduler():
    """
    Shut down the billing scheduler cleanly.
    """
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[BillingScheduler] Scheduler stopped.")


def run_billing_check_now(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Trigger immediate check on demand (useful for API triggers or tests).
    """
    db = SessionLocal()
    try:
        return check_and_update_overdue_invoices(db, tenant_id=tenant_id)
    finally:
        db.close()
