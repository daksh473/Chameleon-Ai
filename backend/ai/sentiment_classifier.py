from groq import Groq
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a sentiment analyzer and customer support triager. 
Analyze the user message and return ONLY a JSON with this structure:
{"score": 0.2, "emotion": "frustrated", "intent": "refund_request", "urgency_level": "HIGH"}

Score is 0.0 (very negative) to 1.0 (very positive).
Intents should be things like: refund_request, order_status, complaint, legal_threat, general_inquiry, reschedule_appointment.
Urgency levels: CRITICAL, HIGH, MEDIUM, LOW.
Return ONLY valid JSON. Nothing else."""

def classify_ticket(message: str) -> dict:
    response = client.chat.completions.create(
        model="groq/compound-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ],
        max_tokens=100,
        temperature=0
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        raw = json_match.group()
    return json.loads(raw)

def analyze_sentiment(message: str) -> dict:
    # For backward compatibility
    res = classify_ticket(message)
    return {"score": res.get("score", 0.5), "emotion": res.get("emotion", "neutral")}


def decide_action(score: float) -> str:
    if score < 0.3:
        return "ESCALATE"    # human agent alert
    elif score > 0.7:
        return "UPSELL"      # offer bhejo
    else:
        return "NORMAL"      # normal reply

# Test
if __name__ == "__main__":
    test_messages = [
        "Yeh kya bakwaas service hai!",
        "Theek hai, chalta hai",
        "Bahut acha experience tha, shukriya!",
        "Mera paisa wapas karo abhi",
        "Mujhe aur products dekhne hain"
    ]
    
    print(f"{'Message':<40} {'Score':<8} {'Emotion':<12} {'Action'}")
    print("-" * 75)
    
    for msg in test_messages:
        result = classify_ticket(msg)
        action = decide_action(result.get("score", 0.5))
        print(f"{msg[:38]:<40} {result.get('score'):<8} {result.get('emotion'):<12} {action} {result.get('intent')} {result.get('urgency_level')}")