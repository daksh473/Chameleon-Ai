"""
ROUTING BRAIN — Intelligent message routing based on sentiment + intent.

Analyzes sentiment severity and intent to decide the routing path:
  - Highly negative / urgent -> immediate escalation (priority 5)
  - Ambiguous / medium severity -> queue for human review (priority 3)
  - Neutral / low-complexity -> bot handles auto-reply (priority 1)
"""

# Intent categories that always warrant escalation regardless of score
URGENT_INTENTS = {
    "legal_threat", "account_cancellation", "fraud_report",
    "data_breach", "physical_harm", "refund_request"
}

# Intent categories that are low-complexity and safe for bot handling
SIMPLE_INTENTS = {
    "general_inquiry", "order_status", "greeting",
    "product_info", "faq", "thank_you"
}


def route_message(message: str, sentiment_result: dict) -> dict:
    """
    Decide the routing path for an incoming message.

    Args:
        message: The raw customer message text.
        sentiment_result: Dict from classify_ticket() containing
            score (0.0-1.0), emotion, intent, urgency_level.

    Returns:
        dict: {
            action: "bot_reply" | "escalate" | "queue",
            priority: 1-5,
            reason: str
        }
    """
    score = sentiment_result.get("score", 0.5)
    emotion = sentiment_result.get("emotion", "neutral")
    intent = sentiment_result.get("intent", "general_inquiry")
    urgency = sentiment_result.get("urgency_level", "LOW")

    # ── Rule 1: Critical urgency or dangerous intents → always escalate ──
    if urgency == "CRITICAL" or intent in URGENT_INTENTS:
        return {
            "action": "escalate",
            "priority": 5,
            "reason": f"Critical urgency or high-risk intent detected. "
                      f"Intent: {intent}, Urgency: {urgency}, Score: {score:.2f}"
        }

    # ── Rule 2: Very negative sentiment → escalate ──
    if score < 0.25:
        return {
            "action": "escalate",
            "priority": 5,
            "reason": f"Extremely negative sentiment ({score:.2f}). "
                      f"Emotion: {emotion}. Requires immediate human attention."
        }

    # ── Rule 3: Negative but not critical → escalate with lower priority ──
    if score < 0.35 and urgency in ("HIGH", "MEDIUM"):
        return {
            "action": "escalate",
            "priority": 4,
            "reason": f"Negative sentiment ({score:.2f}) with {urgency} urgency. "
                      f"Emotion: {emotion}, Intent: {intent}."
        }

    # ── Rule 4: Ambiguous zone — medium severity → queue for review ──
    if 0.25 <= score < 0.45 and emotion in ("frustrated", "angry", "uninterested"):
        return {
            "action": "queue",
            "priority": 3,
            "reason": f"Ambiguous sentiment ({score:.2f}) with negative emotion '{emotion}'. "
                      f"Queued for human review. Intent: {intent}."
        }

    if 0.35 <= score < 0.55 and urgency == "MEDIUM":
        return {
            "action": "queue",
            "priority": 2,
            "reason": f"Medium severity ({score:.2f}) with {urgency} urgency. "
                      f"Intent: {intent}. Queued for review."
        }

    # ── Rule 5: Positive / neutral with simple intent → bot handles it ──
    if score >= 0.45 or intent in SIMPLE_INTENTS:
        return {
            "action": "bot_reply",
            "priority": 1,
            "reason": f"Sentiment is stable ({score:.2f}), emotion: {emotion}. "
                      f"Intent '{intent}' is safe for automated response."
        }

    # ── Fallback: queue anything we're not confident about ──
    return {
        "action": "queue",
        "priority": 2,
        "reason": f"Could not confidently categorize. Score: {score:.2f}, "
                  f"Emotion: {emotion}, Intent: {intent}. Queued for safety."
    }
