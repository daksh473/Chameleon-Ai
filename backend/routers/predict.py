from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
import traceback
from database import get_predictions_cache, set_predictions_cache, CACHE_TTL_SECONDS
from ai.predictive_ai import (
    compute_churn_risks, compute_upsell_opportunities, compute_ticket_forecast,
    compute_revenue_forecast, compute_sentiment_forecast, compute_at_risk_customers,
    compute_best_contact_time, compute_full_dashboard,
)

router = APIRouter(prefix="/predict", tags=["Predictions"])


def _cached_or_compute(cache_key: str, compute_fn, force: bool = False):
    if not force:
        cached = get_predictions_cache(cache_key)
        if cached and not cached["expired"]:
            return {**cached["data"], "cached": True, "calculated_at": cached["calculated_at"]}

    data = compute_fn()
    payload = {**data, "cached": False, "calculated_at": datetime.now().isoformat()}
    set_predictions_cache(cache_key, payload)
    return payload


@router.post("/churn-risk")
def churn_risk(force: bool = Query(False)):
    return _cached_or_compute("churn_risk", lambda: {"customers": compute_churn_risks()}, force)


@router.post("/upsell-opportunities")
def upsell_opportunities(force: bool = Query(False)):
    return _cached_or_compute("upsell", lambda: {"opportunities": compute_upsell_opportunities()}, force)


@router.post("/ticket-forecast")
def ticket_forecast(force: bool = Query(False)):
    return _cached_or_compute("ticket_forecast", compute_ticket_forecast, force)


@router.post("/revenue-forecast")
def revenue_forecast(force: bool = Query(False)):
    return _cached_or_compute("revenue_forecast", compute_revenue_forecast, force)


@router.post("/sentiment-forecast")
def sentiment_forecast(force: bool = Query(False)):
    return _cached_or_compute("sentiment_forecast", compute_sentiment_forecast, force)


@router.post("/at-risk-customers")
def at_risk_customers(force: bool = Query(False)):
    return _cached_or_compute("at_risk", lambda: {"customers": compute_at_risk_customers()}, force)


@router.post("/best-time-to-contact/{customer_id}")
def best_time_to_contact(customer_id: int, force: bool = Query(False)):
    cache_key = f"contact_time_{customer_id}"
    if not force:
        cached = get_predictions_cache(cache_key)
        if cached and not cached["expired"]:
            return {**cached["data"], "cached": True, "calculated_at": cached["calculated_at"]}

    data = compute_best_contact_time(customer_id)
    payload = {**data, "customer_id": customer_id, "cached": False, "calculated_at": datetime.now().isoformat()}
    set_predictions_cache(cache_key, payload)
    return payload


@router.get("/dashboard")
def prediction_dashboard(force: bool = Query(False)):
    try:
        if not force:
            cached = get_predictions_cache("dashboard")
            if cached and not cached["expired"]:
                return {**cached["data"], "cached": True, "calculated_at": cached["calculated_at"]}

        data = compute_full_dashboard(use_ai=True)
        set_predictions_cache("dashboard", data)
        return {**data, "cached": False}
    except Exception as e:
        print("Prediction dashboard error:")
        traceback.print_exc()
        return {
            "churn_risk": [], "upsell_opportunities": [], "ticket_forecast": {}, 
            "revenue_forecast": {}, "sentiment_forecast": {}, "at_risk_customers": [], 
            "ai_insights": [], "summary": {}, "cached": False, "error": str(e)
        }


@router.post("/dashboard/recalculate")
def recalculate_dashboard():
    """Force refresh all predictions."""
    data = compute_full_dashboard(use_ai=True)
    set_predictions_cache("dashboard", data)
    for key, fn in [
        ("churn_risk", lambda: {"customers": compute_churn_risks()}),
        ("upsell", lambda: {"opportunities": compute_upsell_opportunities()}),
        ("ticket_forecast", compute_ticket_forecast),
        ("revenue_forecast", compute_revenue_forecast),
        ("sentiment_forecast", compute_sentiment_forecast),
        ("at_risk", lambda: {"customers": compute_at_risk_customers()}),
    ]:
        set_predictions_cache(key, {**fn(), "calculated_at": datetime.now().isoformat()})
    return {**data, "cached": False, "recalculated": True}
