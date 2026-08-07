"""
RESPONSE ADAPTER — Adjusts reply tone based on channel and sentiment severity.

Wraps the existing generate_reply() function but injects dynamic
channel-specific and tone-specific instructions into the prompt before
generating the final reply.
"""

from ai.bot_reply import generate_reply


# Channel-specific tone instructions
CHANNEL_TONE = {
    "email": (
        "You are responding via EMAIL. Use a formal, structured tone. "
        "Include a proper greeting and sign-off. Use complete sentences "
        "and professional language. Keep it concise but polished. "
        "Format with paragraphs if needed."
    ),
    "telegram": (
        "You are responding via TELEGRAM. Use a casual, concise tone. "
        "Keep messages short and conversational — no more than 2-3 sentences. "
        "Use friendly language. Emojis are acceptable where appropriate. "
        "No formal greetings or sign-offs needed."
    ),
    "dashboard": (
        "You are responding via the live chat dashboard. "
        "Use a professional but warm tone. Keep it under 2 sentences."
    ),
}

# Sentiment-based tone modifiers
SENTIMENT_TONE = {
    "empathetic_urgent": (
        "The customer is clearly upset or frustrated. "
        "Lead with sincere empathy and validation of their feelings. "
        "Acknowledge the problem explicitly before offering any solution. "
        "Do NOT be dismissive. Show urgency in resolving their issue."
    ),
    "empathetic_moderate": (
        "The customer seems somewhat dissatisfied. "
        "Be understanding and reassuring. Acknowledge their concern "
        "and offer clear next steps."
    ),
    "standard": (
        "The customer has a normal query. "
        "Be helpful, clear, and professional."
    ),
    "positive": (
        "The customer is in a good mood or expressing satisfaction. "
        "Match their positive energy. Be warm and appreciative."
    ),
}


def _get_sentiment_tone(score: float, emotion: str) -> str:
    """Select the appropriate tone modifier based on sentiment analysis."""
    if score < 0.25 or emotion in ("angry", "frustrated"):
        return SENTIMENT_TONE["empathetic_urgent"]
    elif score < 0.45 or emotion in ("uninterested",):
        return SENTIMENT_TONE["empathetic_moderate"]
    elif score > 0.7 or emotion in ("happy", "grateful"):
        return SENTIMENT_TONE["positive"]
    else:
        return SENTIMENT_TONE["standard"]


def generate_adaptive_reply(
    message: str,
    action: str,
    sentiment_result: dict,
    channel: str,
    user_history: list
) -> str:
    """
    Generate a reply with adaptive tone based on channel and sentiment.

    This wraps the existing generate_reply() function, injecting
    channel + tone context as memory_context so the LLM adjusts
    its response style automatically.

    Args:
        message: The customer's message text.
        action: "ESCALATE", "NORMAL", or "UPSELL" (from decide_action).
        sentiment_result: Dict with score, emotion, intent, urgency_level.
        channel: "email", "telegram", "dashboard", etc.
        user_history: LLM-formatted chat history from memory_store.

    Returns:
        str: The generated reply text with appropriate tone.
    """
    score = sentiment_result.get("score", 0.5)
    emotion = sentiment_result.get("emotion", "neutral")

    # Build the adaptive context string
    channel_instruction = CHANNEL_TONE.get(channel, CHANNEL_TONE["dashboard"])
    sentiment_instruction = _get_sentiment_tone(score, emotion)

    adaptive_context = (
        f"=== CHANNEL TONE ===\n{channel_instruction}\n\n"
        f"=== EMOTIONAL TONE ===\n{sentiment_instruction}\n\n"
        f"=== CUSTOMER CONTEXT ===\n"
        f"Current emotion: {emotion} (score: {score:.2f})\n"
        f"Intent: {sentiment_result.get('intent', 'unknown')}\n"
        f"Urgency: {sentiment_result.get('urgency_level', 'LOW')}"
    )

    # Call the existing generate_reply with our enriched context
    reply = generate_reply(
        message=message,
        action=action,
        history=user_history,
        memory_context=adaptive_context,
        detected_language="en"
    )

    return reply
