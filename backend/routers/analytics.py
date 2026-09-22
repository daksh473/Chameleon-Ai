import os
import re
import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from groq import Groq

from db.session import get_db
from core.tenancy import get_current_tenant_id
from services import analytics_service
from database import (
    get_analytics_overview, get_sentiment_trend, get_emotion_breakdown,
    get_action_distribution, get_hourly_activity, get_all_ticket_issues,
    get_voice_analytics
)

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ==============================================================================
# MULTI-TENANT BMS EXECUTIVE ANALYTICS
# ==============================================================================

@router.get("/executive-dashboard")
def get_executive_dashboard(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Unified executive multi-module dashboard combining CRM, Support, Billing,
    Inventory, Tasks, and real-time Business Health Score.
    Strictly tenant isolated. Zero cross-tenant leakage.
    """
    return analytics_service.get_executive_bms_dashboard(db, tenant_id=tenant_id)


@router.get("/snapshots")
def get_historical_snapshots_endpoint(
    days: int = Query(14, ge=3, le=90, description="Number of historical days to retrieve"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get daily snapshot timeline for charting trends over time.
    """
    return analytics_service.get_historical_snapshots(db, tenant_id=tenant_id, days=days)


@router.post("/snapshots/generate")
def generate_today_snapshot_endpoint(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Capture or update today's AnalyticsSnapshot for the tenant.
    """
    snap = analytics_service.capture_daily_snapshot(db, tenant_id=tenant_id)
    return {
        "message": f"Snapshot for {snap.snapshot_date} captured successfully.",
        "snapshot_id": snap.id,
        "revenue_this_month": float(snap.revenue_this_month),
        "open_tickets": snap.open_tickets,
        "new_leads_this_week": snap.new_leads_this_week,
        "pending_orders": snap.pending_orders,
        "task_completion_rate": snap.task_completion_rate,
    }


# ==============================================================================
# CONVERSATIONAL & SUPPORT INTELLIGENCE (Maintained for Backward Compatibility)
# ==============================================================================

@router.post("/overview")
def analytics_overview():
    return get_analytics_overview()

@router.get("/overview")
def analytics_overview_get():
    return get_analytics_overview()

@router.post("/sentiment-trend")
def sentiment_trend():
    return get_sentiment_trend()

@router.get("/sentiment-trend")
def sentiment_trend_get():
    return get_sentiment_trend()

@router.post("/emotion-breakdown")
def emotion_breakdown():
    return get_emotion_breakdown()

@router.get("/emotion-breakdown")
def emotion_breakdown_get():
    return get_emotion_breakdown()

@router.post("/action-distribution")
def action_distribution():
    return get_action_distribution()

@router.get("/action-distribution")
def action_distribution_get():
    return get_action_distribution()

@router.post("/hourly-activity")
def hourly_activity():
    return get_hourly_activity()

@router.get("/hourly-activity")
def hourly_activity_get():
    return get_hourly_activity()

@router.post("/voice-stats")
def voice_stats():
    return get_voice_analytics()

@router.get("/voice-stats")
def voice_stats_get():
    return get_voice_analytics()

@router.post("/top-issues")
def top_issues():
    issues = get_all_ticket_issues()
    if not issues:
        return [{"issue": "No tickets yet", "count": 0}]
    
    issues_text = "\n".join(issues)
    prompt = f"""Analyze the following customer support ticket issues and identify the top 5 most recurring themes/categories.
For each theme, estimate how many tickets match it.

Ticket issues:
{issues_text}

Return STRICTLY a JSON array (no markdown, no code fences, just raw JSON):
[
  {{"issue": "Theme name", "count": estimated_count}},
  ...
]
Return exactly 5 items, sorted by count descending."""

    try:
        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            content = json_match.group()
        return json.loads(content)
    except Exception as e:
        print("Top Issues AI Error:", e)
        return [{"issue": "Analysis unavailable", "count": 0}]

@router.post("/customer-health-score")
def customer_health_score():
    overview = get_analytics_overview()
    
    prompt = f"""You are a customer experience analyst. Based on these metrics, compute a Customer Health Score (0-100) and provide insights.

Metrics:
- Total Conversations: {overview['total_conversations']}
- Total Tickets: {overview['total_tickets']}
- Resolution Rate: {overview['resolution_rate']}%
- Average Sentiment Score: {overview['avg_sentiment_score']} (0 = very negative, 1 = very positive)
- Escalation Rate: {overview['escalation_rate']}%
- Upsell Rate: {overview['upsell_rate']}%

Rules:
- Health Score formula: Start with 50. Add points for high sentiment (>0.6), high resolution rate (>70%), high upsell rate. Subtract points for high escalation rate (>20%), low sentiment (<0.4).
- Trend: "improving" if sentiment > 0.6, "declining" if sentiment < 0.35, else "stable".
- Provide exactly 3 short key insights (1 sentence each).

Return STRICTLY a JSON object (no markdown, no code fences, just raw JSON):
{{
  "score": int,
  "trend": "improving" | "declining" | "stable",
  "key_insights": ["insight1", "insight2", "insight3"]
}}"""

    try:
        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group()
        return json.loads(content)
    except Exception as e:
        print("Health Score AI Error:", e)
        return {
            "score": 50,
            "trend": "stable",
            "key_insights": [
                "Insufficient data for detailed analysis.",
                "Continue monitoring sentiment trends.",
                "Focus on reducing escalation rate."
            ]
        }
