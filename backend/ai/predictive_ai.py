import os
import json
import re
from datetime import datetime, timedelta
from groq import Groq
from dotenv import load_dotenv
from typing import Optional

from database import (
    get_customers, get_deals, get_customer, get_customer_timeline,
    get_conversations_since, get_tickets_since, get_open_tickets_for_customer,
    get_ticket_weekday_distribution, get_daily_ticket_counts, get_daily_sentiment,
    get_customer_activity_hours, match_customer_conversations,
)

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "groq/compound-mini"

DOW_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _days_since(iso_date: str) -> int:
    if not iso_date:
        return 999
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", ""))
        return (datetime.now() - dt).days
    except Exception:
        return 999


def _sentiment_trend(scores: list) -> str:
    if len(scores) < 2:
        return "stable"
    mid = len(scores) // 2
    first = sum(scores[:mid]) / max(len(scores[:mid]), 1)
    second = sum(scores[mid:]) / max(len(scores[mid:]), 1)
    if second - first > 0.08:
        return "improving"
    if first - second > 0.08:
        return "declining"
    return "stable"


def _risk_factor_chips(factors: dict) -> list:
    chips = []
    if factors.get("declining_sentiment"):
        chips.append("Declining Sentiment")
    if factors.get("no_contact_7d"):
        chips.append("No Contact 7d+")
    if factors.get("no_contact_14d"):
        chips.append("No Contact 14d+")
    if factors.get("open_tickets", 0) > 0:
        chips.append(f"{factors['open_tickets']} Open Ticket(s)")
    if factors.get("high_ticket_freq"):
        chips.append("High Ticket Frequency")
    if factors.get("low_sentiment"):
        chips.append("Low Avg Sentiment")
    if factors.get("escalations", 0) > 0:
        chips.append(f"{factors['escalations']} Escalation(s)")
    return chips or ["Moderate Risk Signals"]


def _get_active_customers(customers, conversations):
    if customers:
        return customers
    if conversations:
        session_map = {}
        for c in conversations:
            sid = c.get("session_id", "unknown")
            if sid not in session_map:
                session_map[sid] = []
            session_map[sid].append(c)
        pseudo_customers = []
        for i, (sid, convs) in enumerate(session_map.items()):
            scores = [x["sentiment_score"] for x in convs if x.get("sentiment_score") is not None]
            avg_sent = sum(scores) / len(scores) if scores else 0.5
            pseudo_customers.append({
                "id": f"pseudo-{i}",
                "name": f"User {sid[:6]}" if sid != "unknown" else "Unknown User",
                "session_id": sid,
                "email": f"{sid[:6]}@example.com" if sid != "unknown" else "",
                "last_contact": convs[-1]["timestamp"],
                "avg_sentiment": avg_sent
            })
        return pseudo_customers
    return [
        {"id": "demo-1", "name": "Demo User 1", "email": "demo1@example.com", "last_contact": (datetime.now() - timedelta(days=5)).isoformat(), "avg_sentiment": 0.3},
        {"id": "demo-2", "name": "Demo User 2", "email": "demo2@example.com", "last_contact": datetime.now().isoformat(), "avg_sentiment": 0.85}
    ]

def compute_churn_risks(use_ai: bool = True) -> list:
    customers = get_customers()
    conversations = get_conversations_since(30)
    tickets = get_tickets_since(30)
    customers = _get_active_customers(customers, conversations)
    results = []

    for c in customers:
        cust_convs = match_customer_conversations(c, conversations)
        scores = [x["sentiment_score"] for x in cust_convs if x.get("sentiment_score") is not None]
        trend = _sentiment_trend(scores)
        avg_sent = sum(scores) / len(scores) if scores else (c.get("avg_sentiment") or 0.5)
        days_inactive = _days_since(c.get("last_contact") or c.get("created_at"))
        open_tk = get_open_tickets_for_customer(c.get("name", ""))
        cust_tickets = [t for t in tickets if c.get("name", "").lower() in (t.get("customer_name") or "").lower()]
        escalations = sum(1 for x in cust_convs if x.get("action") == "ESCALATE")

        prob = 0.1
        factors = {
            "declining_sentiment": trend == "declining",
            "no_contact_3d": days_inactive > 3,
            "no_contact_7d": days_inactive >= 7,
            "no_contact_14d": days_inactive >= 14,
            "open_tickets": open_tk,
            "high_ticket_freq": len(cust_tickets) >= 3,
            "low_sentiment": avg_sent < 0.4,
            "escalations": escalations,
        }

        if trend == "declining" or days_inactive > 3:
            prob = max(prob, 0.75)

        prob += max(0, (0.5 - avg_sent) * 0.6)
        if trend == "declining":
            prob += 0.2
        if days_inactive >= 7:
            prob += 0.12
        if days_inactive >= 14:
            prob += 0.15
        if open_tk:
            prob += min(0.1 * open_tk, 0.25)
        if len(cust_tickets) >= 3:
            prob += 0.12
        if escalations:
            prob += min(0.08 * escalations, 0.2)

        prob = round(min(max(prob, 0.05), 0.98), 3)
        risk_factors = _risk_factor_chips(factors)

        results.append({
            "customer_id": c["id"],
            "name": c["name"],
            "email": c.get("email") or "",
            "last_contact": c.get("last_contact") or c.get("created_at"),
            "sentiment_trend": trend,
            "churn_probability": prob,
            "risk_factors": risk_factors,
            "recommended_action": _default_churn_action(prob, factors),
            "avg_sentiment": round(avg_sent, 3),
        })

    results.sort(key=lambda x: x["churn_probability"], reverse=True)

    if use_ai and results:
        top = _groq_enrich_churn(results[:15])
        return top + results[15:]

    return results


def _default_churn_action(prob: float, factors: dict) -> str:
    if prob >= 0.7:
        return "Contact immediately with retention offer and personal follow-up"
    if factors.get("open_tickets"):
        return "Resolve open tickets and send proactive status update"
    if factors.get("no_contact_7d"):
        return "Send check-in email to re-engage customer"
    if factors.get("declining_sentiment"):
        return "Schedule call to address concerns before they escalate"
    return "Monitor closely and maintain regular touchpoints"


def _groq_enrich_churn(top_customers: list) -> list:
    summary = json.dumps([{
        "name": c["name"], "churn_probability": c["churn_probability"],
        "risk_factors": c["risk_factors"], "sentiment_trend": c["sentiment_trend"]
    } for c in top_customers[:10]])

    prompt = f"""Analyze these at-risk customers and improve their recommended_action with specific WHY explanations.
For each customer add "ai_explanation" (1 sentence why they might churn).

Customers: {summary}

Return JSON array with same length, each item:
{{"name": "...", "recommended_action": "...", "ai_explanation": "..."}}
Only return valid JSON array."""

    try:
        resp = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}],
            max_tokens=800, temperature=0.3
        )
        text = resp.choices[0].message.content.strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            text = json_match.group()
        enriched = json.loads(text)
        name_map = {e["name"]: e for e in enriched if isinstance(e, dict)}
        for c in top_customers:
            if c["name"] in name_map:
                e = name_map[c["name"]]
                c["recommended_action"] = e.get("recommended_action", c["recommended_action"])
                c["ai_explanation"] = e.get("ai_explanation", "")
    except Exception as ex:
        print(f"Churn AI enrich error: {ex}")

    return top_customers


def compute_upsell_opportunities(use_ai: bool = True) -> list:
    customers = get_customers()
    conversations = get_conversations_since(30)
    customers = _get_active_customers(customers, conversations)
    results = []

    for c in customers:
        cust_convs = match_customer_conversations(c, conversations)
        scores = [x["sentiment_score"] for x in cust_convs if x.get("sentiment_score") is not None]
        trend = _sentiment_trend(scores)
        avg_sent = sum(scores) / len(scores) if scores else (c.get("avg_sentiment") or 0.5)
        upsell_actions = sum(1 for x in cust_convs if x.get("action") == "UPSELL")
        engagement = len(cust_convs)

        prob = 0.1
        if avg_sent > 0.7:
            prob = max(prob, 0.8)
        else:
            if trend == "improving":
                prob += 0.2
            if engagement >= 5:
                prob += 0.15
            if upsell_actions:
                prob += 0.15
            if c.get("status") == "customer":
                prob += 0.1
            if c.get("revenue_generated", 0) > 0:
                prob += 0.1

        prob = round(min(max(prob, 0.05), 0.95), 3)
        if prob < 0.35:
            continue

        best_day = "Tuesday" if engagement > 0 else "Wednesday"
        best_hour = "10:00 AM"
        activity = get_customer_activity_hours(c["id"])
        if activity:
            top = activity[0]
            best_day = DOW_NAMES[top["dow"]]
            best_hour = f"{top['hour']:02d}:00"

        results.append({
            "customer_id": c["id"],
            "name": c["name"],
            "company": c.get("company") or "",
            "email": c.get("email") or "",
            "upsell_probability": prob,
            "best_offer": _default_upsell_offer(c, avg_sent),
            "best_time_to_contact": f"{best_day} at {best_hour}",
            "sentiment_trend": trend,
            "engagement_score": engagement,
        })

    results.sort(key=lambda x: x["upsell_probability"], reverse=True)

    if use_ai and results:
        results = _groq_enrich_upsell(results[:12])

    return results


def _default_upsell_offer(customer: dict, avg_sent: float) -> str:
    if avg_sent >= 0.8:
        return "Premium plan upgrade with 15% loyalty discount"
    if customer.get("company"):
        return f"Enterprise bundle for {customer['company']}"
    return "Pro tier upgrade with extended support included"


def _groq_enrich_upsell(opportunities: list) -> list:
    prompt = f"""For these upsell-ready customers, suggest personalized best_offer (short, specific).
Customers: {json.dumps([{'name': o['name'], 'company': o['company'], 'upsell_probability': o['upsell_probability']} for o in opportunities])}

Return JSON array: [{{"name": "...", "best_offer": "..."}}]"""

    try:
        resp = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}],
            max_tokens=500, temperature=0.5
        )
        text = resp.choices[0].message.content.strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            text = json_match.group()
        enriched = json.loads(text)
        name_map = {e["name"]: e.get("best_offer") for e in enriched if isinstance(e, dict)}
        for o in opportunities:
            if o["name"] in name_map:
                o["best_offer"] = name_map[o["name"]]
    except Exception as ex:
        print(f"Upsell AI enrich error: {ex}")
    return opportunities


def compute_ticket_forecast(use_ai: bool = True) -> dict:
    weekday_dist = get_ticket_weekday_distribution(90)
    daily = get_daily_ticket_counts(30)
    
    if not daily:
        conversations = get_conversations_since(30)
        escalations = [c for c in conversations if c.get("action") == "ESCALATE"]
        if escalations:
            daily_esc = {}
            for e in escalations:
                dt = e["timestamp"][:10]
                daily_esc[dt] = daily_esc.get(dt, 0) + 1
            daily = [{"date": k, "count": v} for k, v in daily_esc.items()]
            for e in escalations:
                try:
                    dow = datetime.fromisoformat(e["timestamp"].replace("Z", "")).weekday()
                    weekday_dist[dow] = weekday_dist.get(dow, 0) + 1
                except:
                    pass
        else:
            daily = [{"date": (datetime.now() - timedelta(days=i)).isoformat()[:10], "count": 2} for i in range(7)]
            weekday_dist = {i: 1 for i in range(7)}

    total_weekday = sum(weekday_dist.values()) or 1
    avg_daily = sum(d["count"] for d in daily) / max(len(daily), 1) if daily else 2.0

    next_7 = []
    today = datetime.now().date()
    for i in range(7):
        dt = today + timedelta(days=i + 1)
        dow = dt.weekday()
        dow_sql = (dow + 1) % 7
        dow_factor = weekday_dist.get(dow_sql, 0) / (total_weekday / 7)
        predicted = max(1, round(avg_daily * dow_factor))
        confidence = min(0.92, 0.55 + (len(daily) / 60))
        next_7.append({
            "date": dt.isoformat(),
            "day_name": DOW_NAMES[dow_sql],
            "predicted_tickets": predicted,
            "confidence": round(confidence, 2),
        })

    peak = max(next_7, key=lambda x: x["predicted_tickets"])
    total_predicted = sum(d["predicted_tickets"] for d in next_7)

    recommendation = f"Schedule extra agents on {peak['day_name']} — historically highest ticket volume."

    if use_ai:
        try:
            prompt = f"""Given ticket forecast data: {json.dumps(next_7[:3])}, peak day {peak['day_name']}, 
write one actionable recommendation (1 sentence) for support team staffing."""
            resp = client.chat.completions.create(
                model=MODEL, messages=[{"role": "user", "content": prompt}],
                max_tokens=80, temperature=0.4
            )
            recommendation = resp.choices[0].message.content.strip()
            recommendation = re.sub(r'<think>.*?</think>', '', recommendation, flags=re.DOTALL).strip()
        except Exception:
            pass

    return {
        "next_7_days": next_7,
        "peak_day": peak["day_name"],
        "total_predicted": total_predicted,
        "confidence": round(sum(d["confidence"] for d in next_7) / 7, 2),
        "recommendation": recommendation,
        "avg_daily_baseline": round(avg_daily, 1),
    }


def compute_revenue_forecast(use_ai: bool = True) -> dict:
    deals = get_deals()
    open_deals = [d for d in deals if d.get("stage") not in ("won", "lost")]

    base_30 = sum(d["value"] * (d.get("probability", 50) / 100) for d in open_deals
                  if d.get("expected_close") and _days_until(d["expected_close"]) <= 30)
    base_60 = sum(d["value"] * (d.get("probability", 50) / 100) for d in open_deals
                  if d.get("expected_close") and _days_until(d["expected_close"]) <= 60)
    base_90 = sum(d["value"] * (d.get("probability", 50) / 100) for d in open_deals
                  if d.get("expected_close") and _days_until(d["expected_close"]) <= 90)

    if not open_deals:
        conversations = get_conversations_since(30)
        conv_count = len(conversations) if conversations else 10
        base_30 = conv_count * 1500
        base_60 = base_30 * 1.8
        base_90 = base_30 * 2.5

    result = {
        "30_days": round(base_30, 2),
        "60_days": round(base_60, 2),
        "90_days": round(base_90, 2),
        "confidence": 0.72 if open_deals else 0.45,
        "key_assumptions": [
            f"{len(open_deals)} active deals in pipeline",
            "Conversion rates based on deal stage probability",
            "Historical close rates applied to expected close dates",
        ],
        "trend": "up" if base_60 > base_30 else "down",
    }

    if use_ai and open_deals:
        try:
            from ai.crm_ai import generate_forecast
            ai_forecast = generate_forecast(open_deals)
            if ai_forecast.get("forecast"):
                fc = ai_forecast["forecast"]
                result["30_days"] = fc.get("30_days", result["30_days"])
                result["60_days"] = fc.get("60_days", result["60_days"])
                result["90_days"] = fc.get("90_days", result["90_days"])
                result["confidence"] = 0.78
        except Exception as ex:
            print(f"Revenue AI error: {ex}")

    return result


def _days_until(date_str: str) -> int:
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "")).date()
        return (dt - datetime.now().date()).days
    except Exception:
        return 999


def compute_sentiment_forecast(use_ai: bool = True) -> dict:
    daily = get_daily_sentiment(14)
    if not daily:
        daily = [{"date": (datetime.now() - timedelta(days=i)).date().isoformat(), "avg_score": 0.5} for i in range(7, 0, -1)]

    scores = [d["avg_score"] for d in daily]
    trend = _sentiment_trend(scores)
    last_score = scores[-1] if scores else 0.5
    delta = (scores[-1] - scores[0]) if len(scores) >= 2 else 0

    next_7 = []
    today = datetime.now().date()
    for i in range(7):
        dt = today + timedelta(days=i + 1)
        drift = delta / max(len(scores), 1) * (i + 1)
        predicted = round(min(max(last_score + drift, 0.1), 0.95), 3)
        next_7.append({
            "date": dt.isoformat(),
            "predicted_sentiment": predicted,
            "confidence_upper": round(min(predicted + 0.08, 0.99), 3),
            "confidence_lower": round(max(predicted - 0.08, 0.05), 3),
        })

    trend_direction = trend if trend != "stable" else ("improving" if delta > 0 else "declining" if delta < 0 else "stable")

    if use_ai:
        try:
            prompt = f"""Past sentiment scores: {scores[-7:]}. Predict if next week trend is improving/declining/stable.
Return JSON: {{"trend_direction": "...", "summary": "one sentence"}}"""
            resp = client.chat.completions.create(
                model=MODEL, messages=[{"role": "user", "content": prompt}],
                max_tokens=100, temperature=0.3
            )
            text = resp.choices[0].message.content.strip()
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group()
            ai = json.loads(text)
            trend_direction = ai.get("trend_direction", trend_direction)
        except Exception:
            pass

    actual = [{"date": d["date"], "actual_sentiment": d["avg_score"]} for d in daily[-7:]]

    return {
        "next_7_days": next_7,
        "trend_direction": trend_direction,
        "actual_last_7_days": actual,
        "current_avg": round(last_score, 3),
    }


def compute_at_risk_customers() -> list:
    churn = compute_churn_risks(use_ai=False)
    results = []
    for c in churn:
        days_inactive = _days_since(c.get("last_contact"))
        urgency = c["churn_probability"] * 100
        if c["risk_factors"] and "Open Ticket" in " ".join(c["risk_factors"]):
            urgency += 15
        if days_inactive >= 7:
            urgency += 10
        if c["sentiment_trend"] == "declining":
            urgency += 12
        urgency = round(min(urgency, 100), 1)
        results.append({
            **c,
            "urgency_score": urgency,
            "days_inactive": days_inactive,
        })
    results.sort(key=lambda x: x["urgency_score"], reverse=True)
    return results


def compute_best_contact_time(customer_id: int, use_ai: bool = True) -> dict:
    customer = get_customer(customer_id)
    if not customer:
        return {"best_day": "Tuesday", "best_hour": "10:00", "reason": "Default business hours"}

    activity = get_customer_activity_hours(customer_id)
    conversations = match_customer_conversations(customer, get_conversations_since(60))

    if activity:
        top = activity[0]
        best_day = DOW_NAMES[top["dow"]]
        best_hour = f"{top['hour']:02d}:00"
        reason = f"Customer most active on {best_day}s around {best_hour} based on {top['count']} past interactions"
    elif conversations:
        hours = {}
        for c in conversations:
            try:
                h = datetime.fromisoformat(c["timestamp"].replace("Z", "")).hour
                dow = datetime.fromisoformat(c["timestamp"].replace("Z", "")).weekday()
                key = (dow, h)
                hours[key] = hours.get(key, 0) + 1
            except Exception:
                pass
        if hours:
            top_key = max(hours, key=hours.get)
            best_day = DOW_NAMES[(top_key[0] + 1) % 7]
            best_hour = f"{top_key[1]:02d}:00"
            reason = f"Inferred from chat activity patterns on {best_day}"
        else:
            best_day, best_hour = "Wednesday", "11:00"
            reason = "Limited data — recommended mid-week morning contact"
    else:
        best_day, best_hour = "Tuesday", "10:00"
        reason = "No interaction history — default optimal business hours"

    if use_ai:
        try:
            timeline = get_customer_timeline(customer_id)[:5]
            prompt = f"""Customer {customer['name']}, activity pattern: {best_day} {best_hour}.
Recent: {json.dumps([t.get('description','')[:50] for t in timeline])}
Write a 1-sentence reason why this is the best time to contact. Return JSON: {{"reason": "..."}}"""
            resp = client.chat.completions.create(
                model=MODEL, messages=[{"role": "user", "content": prompt}],
                max_tokens=80, temperature=0.4
            )
            text = resp.choices[0].message.content.strip()
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group()
            ai = json.loads(text)
            reason = ai.get("reason", reason)
        except Exception:
            pass

    return {"best_day": best_day, "best_hour": best_hour, "reason": reason}


def generate_ai_insights(dashboard_data: dict) -> list:
    summary = {
        "at_risk_count": len([c for c in dashboard_data.get("at_risk_customers", []) if c.get("urgency_score", 0) > 60]),
        "upsell_count": len(dashboard_data.get("upsell_opportunities", [])),
        "ticket_forecast": dashboard_data.get("ticket_forecast", {}).get("total_predicted"),
        "peak_day": dashboard_data.get("ticket_forecast", {}).get("peak_day"),
        "sentiment_trend": dashboard_data.get("sentiment_forecast", {}).get("trend_direction"),
        "revenue_30": dashboard_data.get("revenue_forecast", {}).get("30_days"),
    }

    prompt = f"""Based on this predictive analytics summary, generate exactly 5 strategic insights for a customer support team.
Summary: {json.dumps(summary)}

Return JSON array of 5 items:
[{{"icon": "alert|trend|users|ticket|revenue", "text": "insight sentence", "priority": "high|medium|low", "action": "button label"}}]"""

    try:
        resp = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}],
            max_tokens=600, temperature=0.5
        )
        text = resp.choices[0].message.content.strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            text = json_match.group()
        return json.loads(text)
    except Exception as ex:
        print(f"Insights AI error: {ex}")
        return _fallback_insights(dashboard_data)


def _fallback_insights(data: dict) -> list:
    at_risk = len([c for c in data.get("at_risk_customers", []) if c.get("churn_probability", 0) > 0.7])
    upsell = len(data.get("upsell_opportunities", []))
    peak = data.get("ticket_forecast", {}).get("peak_day", "Tuesday")
    trend = data.get("sentiment_forecast", {}).get("trend_direction", "stable")
    insights = []
    if at_risk:
        insights.append({"icon": "alert", "text": f"{at_risk} customers at high churn risk — reach out before they leave", "priority": "high", "action": "View At-Risk"})
    if upsell:
        insights.append({"icon": "trend", "text": f"{upsell} customers show strong upsell signals — launch targeted campaign", "priority": "medium", "action": "View Upsell"})
    insights.append({"icon": "ticket", "text": f"{peak} historically has highest ticket volume — schedule extra agents", "priority": "medium", "action": "View Forecast"})
    if trend == "improving":
        insights.append({"icon": "users", "text": "Sentiment is improving week-over-week — good time for upsell campaign", "priority": "low", "action": "Send Offers"})
    elif trend == "declining":
        insights.append({"icon": "alert", "text": "Sentiment trending down — prioritize proactive outreach", "priority": "high", "action": "Contact Now"})
    insights.append({"icon": "revenue", "text": f"₹{data.get('revenue_forecast', {}).get('30_days', 0):,.0f} predicted revenue next 30 days", "priority": "low", "action": "View Pipeline"})
    return insights[:5]


def compute_full_dashboard(use_ai: bool = True) -> dict:
    churn = compute_churn_risks(use_ai=use_ai)
    upsell = compute_upsell_opportunities(use_ai=use_ai)
    tickets = compute_ticket_forecast(use_ai=use_ai)
    revenue = compute_revenue_forecast(use_ai=use_ai)
    sentiment = compute_sentiment_forecast(use_ai=use_ai)
    at_risk = compute_at_risk_customers()

    confidences = [
        tickets.get("confidence", 0.5),
        revenue.get("confidence", 0.5),
        0.75 if churn else 0.5,
    ]
    overall_confidence = round(sum(confidences) / len(confidences) * 100, 1)

    partial = {
        "churn_risk": churn,
        "upsell_opportunities": upsell,
        "ticket_forecast": tickets,
        "revenue_forecast": revenue,
        "sentiment_forecast": sentiment,
        "at_risk_customers": at_risk,
    }
    insights = generate_ai_insights(partial)

    return {
        **partial,
        "ai_insights": insights,
        "overall_confidence": overall_confidence,
        "calculated_at": datetime.now().isoformat(),
        "summary": {
            "at_risk_count": len([c for c in churn if c["churn_probability"] > 0.5]),
            "upsell_count": len(upsell),
            "tickets_this_week": tickets.get("total_predicted", 0),
            "revenue_30_days": revenue.get("30_days", 0),
            "sentiment_trend": sentiment.get("trend_direction"),
        },
    }
