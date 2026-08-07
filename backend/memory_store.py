"""
MEMORY STORE — Cross-channel conversation memory keyed by unified user identity.

Stores interaction history in a local JSON file (cross_channel_memory.json)
so the AI agent "remembers" if a user complained on Email and followed up on Telegram.

Architecture is swappable — replace the JSON backend with SQLite/Redis later
by only changing the internal _load / _save methods.
"""

import json
import os
import threading
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "cross_channel_memory.json")

# Thread lock for safe concurrent read/write
_lock = threading.Lock()


def _load_store() -> dict:
    """Load the entire memory store from disk."""
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_store(store: dict):
    """Persist the entire memory store to disk."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def get_user_context(user_id: str) -> list:
    """
    Retrieve the full cross-channel conversation history for a user.

    Args:
        user_id: Unified identifier (email address, telegram ID, etc.)

    Returns:
        list: Chronological list of interaction dicts, each containing:
            { channel, message, direction, timestamp }
    """
    with _lock:
        store = _load_store()
        return store.get(user_id, {}).get("history", [])


def get_user_context_as_chat_history(user_id: str) -> list:
    """
    Format user history as LLM-compatible chat messages.

    Returns:
        list of {"role": "user"|"assistant", "content": "..."}
    """
    raw_history = get_user_context(user_id)
    formatted = []
    for entry in raw_history[-20:]:  # Last 20 interactions for context window
        role = "user" if entry.get("direction") == "inbound" else "assistant"
        channel_tag = f"[{entry.get('channel', 'unknown').upper()}] "
        formatted.append({
            "role": role,
            "content": channel_tag + entry.get("message", "")
        })
    return formatted


def append_to_user_history(user_id: str, channel: str, message: str, direction: str):
    """
    Append a message to a user's unified cross-channel history.

    Args:
        user_id: Unified identifier.
        channel: "email", "telegram", "dashboard", etc.
        message: The message text.
        direction: "inbound" (from customer) or "outbound" (our reply).
    """
    entry = {
        "channel": channel,
        "message": message,
        "direction": direction,
        "timestamp": datetime.now().isoformat()
    }

    with _lock:
        store = _load_store()

        if user_id not in store:
            store[user_id] = {
                "first_seen": datetime.now().isoformat(),
                "channels_used": [],
                "history": []
            }

        user_data = store[user_id]

        # Track which channels this user has used
        if channel not in user_data.get("channels_used", []):
            user_data.setdefault("channels_used", []).append(channel)

        user_data["last_seen"] = datetime.now().isoformat()
        user_data["history"].append(entry)

        # Cap history at 200 entries per user to prevent unbounded growth
        if len(user_data["history"]) > 200:
            user_data["history"] = user_data["history"][-200:]

        _save_store(store)


def get_user_summary(user_id: str) -> str:
    """
    Generate a brief text summary of a user's cross-channel activity
    for injection into LLM context.
    """
    with _lock:
        store = _load_store()
        user_data = store.get(user_id)

    if not user_data:
        return "New user — no prior interaction history."

    history = user_data.get("history", [])
    channels = user_data.get("channels_used", [])
    total = len(history)

    summary_parts = [
        f"Returning user with {total} prior interactions.",
        f"Channels used: {', '.join(channels)}.",
    ]

    # Show last 3 messages as quick context
    recent = history[-3:] if len(history) >= 3 else history
    if recent:
        summary_parts.append("Recent messages:")
        for entry in recent:
            direction = "Customer" if entry["direction"] == "inbound" else "Agent"
            summary_parts.append(
                f"  [{entry['channel'].upper()}] {direction}: {entry['message'][:80]}"
            )

    return "\n".join(summary_parts)
