"""
CASPIAN AGENT — Intelligent Communication Layer

This is the central orchestrator that processes every incoming message
from Email/Telegram through a full intelligence pipeline:

  1. Sentiment Analysis   (existing engine)
  2. Routing Brain        (escalate / bot_reply / queue)
  3. Cross-Channel Memory (fetch user history across all channels)
  4. Adaptive Reply       (tone-adjusted based on channel + sentiment)
  5. Explainability Log   (structured trace of every decision)
  6. Send Reply           (via Caspian SDK back to the same channel)
"""

import os
from datetime import datetime

from ai.sentiment_classifier import classify_ticket, decide_action
from ai.bot_reply import generate_reply
from database import save_conversation, create_ticket
from caspian_sdk import CommClient
from dotenv import load_dotenv

# ── New Intelligence Modules ──
from routing_brain import route_message
from memory_store import (
    get_user_context,
    get_user_context_as_chat_history,
    get_user_summary,
    append_to_user_history
)
from response_adapter import generate_adaptive_reply
from explainability_logger import log_decision

load_dotenv()

client = CommClient()

# ═══════════════════════════════════════════════════════════════
#  PIPELINE STAGE LOGGER — Visual pipeline tracing in terminal
# ═══════════════════════════════════════════════════════════════

def _log_stage(stage: str, detail: str):
    """Print a formatted pipeline stage to the terminal."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"  [{timestamp}] ⚙ {stage}: {detail}")


def _log_header(channel: str, sender: str):
    """Print a pipeline start header."""
    print("\n" + "=" * 70)
    print(f"  🔵 CASPIAN PIPELINE — New message from [{channel.upper()}]")
    print(f"  👤 Sender: {sender}")
    print("=" * 70)


def _log_footer(action: str):
    """Print a pipeline end footer."""
    print(f"  ✅ Pipeline complete. Action taken: {action}")
    print("=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════
#  MAIN MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════════

@client.on_message
def handle_message(message):
    text = message.text
    channel = message.channel   # "email" or "telegram"
    sender = message.sender     # customer identifier from that channel
    user_id = sender            # unified identity (email addr or telegram ID)

    _log_header(channel, sender)

    # ── STAGE 1: Sentiment Analysis (existing engine) ──
    try:
        sentiment_result = classify_ticket(text)
    except Exception as e:
        print(f"  ❌ Sentiment analysis failed: {e}")
        sentiment_result = {
            "score": 0.5, "emotion": "neutral",
            "intent": "general_inquiry", "urgency_level": "LOW"
        }

    score = sentiment_result.get("score", 0.5)
    emotion = sentiment_result.get("emotion", "neutral")
    intent = sentiment_result.get("intent", "general_inquiry")
    urgency = sentiment_result.get("urgency_level", "LOW")
    action = decide_action(score)

    _log_stage("SENTIMENT", f"Score={score:.2f}  Emotion={emotion}  Intent={intent}  Urgency={urgency}")
    _log_stage("ACTION", f"Legacy action: {action}")

    # ── STAGE 2: Routing Brain ──
    routing = route_message(text, sentiment_result)
    routing_action = routing["action"]
    routing_priority = routing["priority"]
    routing_reason = routing["reason"]

    _log_stage("ROUTING", f"Decision={routing_action.upper()}  Priority={routing_priority}/5")
    _log_stage("REASON", routing_reason)

    # ── STAGE 3: Cross-Channel Memory ──
    user_history = get_user_context_as_chat_history(user_id)
    user_summary = get_user_summary(user_id)

    _log_stage("MEMORY", f"Found {len(user_history)} prior interactions for user")
    if user_history:
        _log_stage("CONTEXT", user_summary.split("\n")[0])  # First line only

    # Save the inbound message to memory
    append_to_user_history(user_id, channel, text, "inbound")

    # ── STAGE 4: Generate Response (based on routing decision) ──
    reply_text = None

    if routing_action == "bot_reply":
        # Bot handles it — generate an adaptive, tone-aware reply
        reply_text = generate_adaptive_reply(
            message=text,
            action=action,
            sentiment_result=sentiment_result,
            channel=channel,
            user_history=user_history
        )
        _log_stage("REPLY", f"Adaptive bot reply generated ({len(reply_text)} chars)")

    elif routing_action == "escalate":
        # Create a high-priority ticket in the existing ticket system
        create_ticket(
            customer_name=sender,
            issue=text,
            score=score,
            language="en",
            source=f"caspian-{channel}"
        )
        _log_stage("TICKET", f"High-priority ticket created (source: caspian-{channel})")

        # Still generate a reply to acknowledge the customer
        reply_text = generate_adaptive_reply(
            message=text,
            action="ESCALATE",
            sentiment_result=sentiment_result,
            channel=channel,
            user_history=user_history
        )
        _log_stage("REPLY", f"Escalation acknowledgment generated ({len(reply_text)} chars)")

    elif routing_action == "queue":
        # Create a medium-priority ticket for human review
        create_ticket(
            customer_name=sender,
            issue=f"[QUEUED P{routing_priority}] {text}",
            score=score,
            language="en",
            source=f"caspian-{channel}"
        )
        _log_stage("QUEUE", f"Queued for review with priority {routing_priority}")

        # Generate a holding reply
        reply_text = generate_adaptive_reply(
            message=text,
            action="NORMAL",
            sentiment_result=sentiment_result,
            channel=channel,
            user_history=user_history
        )
        _log_stage("REPLY", f"Holding reply generated ({len(reply_text)} chars)")

    # ── STAGE 5: Save to database ──
    save_conversation(
        message=text,
        score=score,
        emotion=emotion,
        action=action,
        reply=reply_text or "",
        channel=f"caspian-{channel}"
    )
    _log_stage("DATABASE", "Conversation saved to conversations table")

    # Save the outbound reply to cross-channel memory
    if reply_text:
        append_to_user_history(user_id, channel, reply_text, "outbound")

    # ── STAGE 6: Explainability Log ──
    log_decision({
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "channel": channel,
        "message_preview": text[:100],
        "sentiment_score": score,
        "emotion": emotion,
        "intent": intent,
        "urgency_level": urgency,
        "routing_action": routing_action,
        "routing_priority": routing_priority,
        "routing_reason": routing_reason,
        "reply_generated": reply_text is not None,
        "reply_preview": (reply_text or "")[:100],
    })
    _log_stage("TRACE", "Decision logged to explainability_trace.jsonl")

    # ── STAGE 7: Send Reply via Caspian ──
    if reply_text:
        message.reply(reply_text)
        _log_stage("SENT", f"Reply delivered via {channel.upper()}")

    _log_footer(routing_action)


# ═══════════════════════════════════════════════════════════════
#  LISTENER ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def start_caspian_listener():
    """Start the Caspian SDK listener — connects to email and telegram."""
    print("\n" + "─" * 70)
    print("  🚀 CASPIAN INTELLIGENT COMMUNICATION LAYER")
    print("  Pipeline: Sentiment → Routing → Memory → Adaptive Reply → Trace")
    print("  Listening for messages on all connected channels...")
    print("─" * 70 + "\n")
    client.listen()
