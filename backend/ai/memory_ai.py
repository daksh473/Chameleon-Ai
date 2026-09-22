import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from typing import List, Dict, Optional
from database import (
    get_memories_for_customer, get_conversation_summary, save_conversation_summary,
    get_conversation_history, get_open_ticket_count_for_customer, get_memory_count,
    store_memory, get_all_tickets, get_all_emails
)

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
PHONE_RE = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
NAME_RE = re.compile(r"(?:my name is|i am|i'm|mera naam|naam hai)\s+([A-Za-z\u0900-\u097F]+)", re.I)


def extract_customer_identifier(message: str, session_id: str, current_id: Optional[str] = None) -> str:
    if current_id and not current_id.startswith("live_"):
        return current_id
    email = EMAIL_RE.search(message)
    if email:
        return email.group(0).lower()
    phone = PHONE_RE.search(message)
    if phone:
        return phone.group(0)
    name = NAME_RE.search(message)
    if name:
        return name.group(1).strip().title()
    return current_id or session_id


def build_memory_context(customer_identifier: str) -> tuple[str, int]:
    memories = get_memories_for_customer(customer_identifier)
    summary = get_conversation_summary(customer_identifier)
    memory_count = len(memories)

    if not memories and not summary:
        return "", 0

    lines = ["Customer history:"]
    if summary:
        lines.append(summary.get("summary", ""))
        if summary.get("common_issues"):
            lines.append(f"Common issues: {', '.join(summary['common_issues'][:5])}")
        if summary.get("preferred_language"):
            lines.append(f"Preferred language: {summary['preferred_language']}")
        if summary.get("personality_traits"):
            traits = summary["personality_traits"]
            trait_str = ", ".join(f"{k}: {v}" for k, v in list(traits.items())[:4])
            lines.append(f"Personality: {trait_str}")

    for mem in memories[:8]:
        lines.append(f"- [{mem['memory_type']}] {mem['key']}: {mem['value']}")

    open_tickets = get_open_ticket_count_for_customer(customer_identifier)
    if open_tickets:
        lines.append(f"They have {open_tickets} open ticket(s).")

    return "\n".join(lines), memory_count


def generate_smart_greeting(customer_identifier: str) -> dict:
    memories = get_memories_for_customer(customer_identifier, limit=10)
    summary = get_conversation_summary(customer_identifier)
    is_returning = len(memories) > 0 or summary is not None

    if not is_returning:
        return {
            "greeting": "Hello! How can I help you today?",
            "is_returning": False,
            "memory_count": 0
        }

    context, count = build_memory_context(customer_identifier)
    prompt = f"""You are a friendly customer service bot greeting a returning customer.
Use this customer history to write a warm, personalized welcome (1-2 sentences).
If they had a complaint before, ask if it was resolved.
Reply in the customer's preferred language (e.g. Hindi, Tamil, Bengali, English, etc.) if known from history. Otherwise reply in English.
Make sure to use the correct regional script if a regional language is preferred.

Customer context:
{context}

Write only the greeting message, nothing else."""

    try:
        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        greeting = response.choices[0].message.content.strip()
        greeting = re.sub(r'<think>.*?</think>', '', greeting, flags=re.DOTALL).strip()
    except Exception:
        last_issue = ""
        if summary and summary.get("common_issues"):
            last_issue = summary["common_issues"][0]
        elif memories:
            complaints = [m for m in memories if m["memory_type"] == "complaint"]
            if complaints:
                last_issue = complaints[0]["value"][:80]
        if last_issue:
            greeting = f"Welcome back! Last time you had an issue with {last_issue}. Has that been resolved? How can I help you today?"
        else:
            greeting = "Welcome back! How can I help you today?"

    return {"greeting": greeting, "is_returning": True, "memory_count": count or len(memories)}


def extract_and_store_memories(session_id: str, customer_identifier: str, message: str, reply: str, score: float):
    prompt = f"""Analyze this customer service exchange and extract memories as JSON array.
Each memory: {{"memory_type": "preference|complaint|purchase|personality|context", "key": "short label", "value": "detail", "importance": 0.0-1.0}}

Customer: {message}
Bot: {reply}
Sentiment score: {score}

Return ONLY a JSON array. If nothing to extract, return [].
Examples: preference for email contact, delivery complaints, name/location, impatient personality, purchase intent.
Make sure to extract any language preference if the customer is speaking in an Indian regional language (e.g. key="preferred_language", value="Hindi")."""

    try:
        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            text = json_match.group()
        memories = json.loads(text)
        for mem in memories:
            if isinstance(mem, dict) and mem.get("key") and mem.get("value"):
                store_memory(
                    session_id, customer_identifier,
                    mem.get("memory_type", "context"),
                    mem["key"], mem["value"],
                    float(mem.get("importance", 0.5))
                )
    except Exception as e:
        print(f"Memory extraction error: {e}")
        if score < 0.4:
            store_memory(session_id, customer_identifier, "complaint", "recent_issue", message[:200], 0.7)


def summarize_customer(customer_identifier: str) -> dict:
    memories = get_memories_for_customer(customer_identifier, limit=30)
    history = get_conversation_history(customer_identifier)
    if not history:
        for sid_mem in memories:
            if sid_mem.get("session_id"):
                history.extend(get_conversation_history(sid_mem["session_id"]))

    conv_text = "\n".join(
        f"{m['role']}: {m['message']}" for m in history[-30:]
    ) if history else "\n".join(f"- {m['value']}" for m in memories)

    prompt = f"""Summarize this customer's interaction history. Return JSON:
{{
  "summary": "2-3 sentence executive summary",
  "total_conversations": number,
  "common_issues": ["issue1", "issue2"],
  "personality_traits": {{"patience": 0.0-1.0, "tech_savvy": 0.0-1.0, "friendliness": 0.0-1.0}},
  "preferred_language": "en or hi",
  "sentiment_trend": "improving|declining|stable"
}}

Data:
{conv_text}
Memories: {json.dumps([{{'type': m['memory_type'], 'value': m['value']}} for m in memories[:15]])}"""

    try:
        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.4
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group()
        data = json.loads(text)
    except Exception:
        data = {
            "summary": f"Customer with {len(memories)} stored memories.",
            "total_conversations": max(1, len(history) // 2),
            "common_issues": [m["value"][:50] for m in memories if m["memory_type"] == "complaint"][:3],
            "personality_traits": {"patience": 0.5, "tech_savvy": 0.5},
            "preferred_language": "en",
            "sentiment_trend": "stable"
        }

    saved = save_conversation_summary(
        customer_identifier,
        data.get("summary", ""),
        data.get("total_conversations", 1),
        data.get("common_issues", []),
        data.get("personality_traits", {}),
        data.get("preferred_language", "en"),
        data.get("sentiment_trend", "stable")
    )
    return saved


def get_customer_profile_for_dashboard(customer_identifier: str) -> dict:
    memories = get_memories_for_customer(customer_identifier, limit=20)
    summary = get_conversation_summary(customer_identifier)
    is_returning = len(memories) > 0

    name = customer_identifier
    for mem in memories:
        if mem["memory_type"] == "context" and "name" in mem["key"].lower():
            name = mem["value"]
            break
        if mem["memory_type"] == "personality":
            continue
    if "@" not in name and not name.startswith("live_"):
        display_name = name
    else:
        display_name = name.split("@")[0].title() if "@" in name else f"Session {customer_identifier[:8]}"

    personality_line = ""
    if summary and summary.get("personality_traits"):
        traits = summary["personality_traits"]
        parts = []
        if traits.get("patience", 0.5) < 0.4:
            parts.append("gets frustrated quickly")
        if traits.get("tech_savvy", 0.5) > 0.7:
            parts.append("technically savvy")
        if traits.get("friendliness", 0.5) > 0.7:
            parts.append("friendly")
        personality_line = ", ".join(parts) if parts else "neutral temperament"
    elif memories:
        personality_line = "returning customer with interaction history"

    common_issues = summary.get("common_issues", []) if summary else []
    if not common_issues:
        common_issues = [m["value"][:40] for m in memories if m["memory_type"] == "complaint"][:3]

    last_visit = summary.get("last_updated") if summary else None
    if not last_visit and memories:
        last_visit = memories[0].get("last_accessed")

    return {
        "customer_identifier": customer_identifier,
        "is_returning": is_returning,
        "display_name": display_name,
        "interaction_count": summary.get("total_conversations", len(memories)) if summary else len(memories),
        "common_issues": common_issues,
        "personality_summary": personality_line or "No personality data yet",
        "last_visit": last_visit,
        "memory_count": get_memory_count(customer_identifier),
        "preferred_language": summary.get("preferred_language", "en") if summary else "en"
    }
