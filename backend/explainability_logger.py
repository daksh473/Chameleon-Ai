"""
EXPLAINABILITY LOGGER — Structured trace of every routing decision and reply.

Logs every pipeline execution as a JSON Lines entry to explainability_trace.jsonl
so each decision can be audited, debugged, and displayed on the dashboard.
"""

import json
import os
import threading
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "explainability_trace.jsonl")

_lock = threading.Lock()


def log_decision(decision_object: dict):
    """
    Append a structured decision trace to the explainability log.

    Args:
        decision_object: Dict containing:
            - timestamp: ISO timestamp
            - user_id: Unified customer identifier
            - channel: email, telegram, dashboard, etc.
            - message_preview: First 100 chars of the message
            - sentiment_score: 0.0 - 1.0
            - emotion: Detected emotion
            - intent: Classified intent
            - urgency_level: CRITICAL / HIGH / MEDIUM / LOW
            - routing_action: escalate / bot_reply / queue
            - routing_priority: 1-5
            - routing_reason: Why this decision was made
            - reply_generated: Whether a reply was sent
            - reply_preview: First 100 chars of the reply (if any)
            - confidence: Confidence in the decision (derived from score clarity)
    """
    # Ensure timestamp exists
    if "timestamp" not in decision_object:
        decision_object["timestamp"] = datetime.now().isoformat()

    # Calculate confidence from how clear the sentiment signal is
    if "confidence" not in decision_object:
        score = decision_object.get("sentiment_score", 0.5)
        # Confidence is high when score is clearly positive or negative,
        # low when it's in the ambiguous middle zone
        distance_from_center = abs(score - 0.5)
        decision_object["confidence"] = round(min(distance_from_center * 2 + 0.3, 1.0), 2)

    with _lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(decision_object, ensure_ascii=False) + "\n")


def get_recent_decisions(limit: int = 50) -> list:
    """
    Read the most recent decision traces from the log.

    Args:
        limit: Maximum number of entries to return.

    Returns:
        list of decision dicts, most recent first.
    """
    if not os.path.exists(LOG_FILE):
        return []

    entries = []
    with _lock:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    # Return most recent first
    return entries[-limit:][::-1]


def get_decisions_for_user(user_id: str, limit: int = 20) -> list:
    """
    Get decision traces for a specific user.

    Args:
        user_id: The unified customer identifier.
        limit: Maximum entries to return.

    Returns:
        list of decision dicts for this user, most recent first.
    """
    all_decisions = get_recent_decisions(limit=500)
    user_decisions = [d for d in all_decisions if d.get("user_id") == user_id]
    return user_decisions[:limit]
