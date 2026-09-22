import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
PHONE_RE = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?(?:\d{10}|\d{3}[-.\s]?\d{3}[-.\s]?\d{4})')
NAME_RE = re.compile(
    r"(?:my name is|i am|i'm|i'm called|call me|this is|mera naam|naam hai|main)\s+([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F\s]{0,30}?)(?:\.|,|!|\?|$|\s+(?:and|from|from|at))",
    re.I
)
COMPANY_RE = re.compile(
    r"(?:i work at|work for|from|company is|employed at|working at)\s+([A-Za-z0-9\u0900-\u097F][A-Za-z0-9\u0900-\u097F\s&.-]{1,40})",
    re.I
)


def _regex_extract(message: str) -> dict:
    result = {"name": None, "email": None, "phone": None, "company": None}
    email = EMAIL_RE.search(message)
    if email:
        result["email"] = email.group(0).lower()
    phone = PHONE_RE.search(message)
    if phone:
        digits = re.sub(r'\D', '', phone.group(0))
        if len(digits) >= 10:
            result["phone"] = digits[-10:] if len(digits) > 10 else digits
    name = NAME_RE.search(message)
    if name:
        result["name"] = name.group(1).strip().title()
    company = COMPANY_RE.search(message)
    if company:
        result["company"] = company.group(1).strip().title()
    return result


def extract_customer_info(message: str) -> dict:
    """Extract name, email, phone, company from a chat message using Groq + regex fallback."""
    regex_result = _regex_extract(message)

    prompt = f"""Extract customer contact information from this chat message.
Return ONLY valid JSON with these fields (use null if not mentioned):
{{
  "name": "full name or first name",
  "email": "email address",
  "phone": "phone number digits only",
  "company": "company or organization name"
}}

Message: "{message}"

Rules:
- name: from phrases like "my name is X", "I am X", "call me X", "mera naam X"
- email: any email address mentioned
- phone: any phone/mobile number mentioned
- company: from "I work at X", "from X company", etc.
- Return null for fields not found. Do not guess."""

    try:
        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.1
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
        for key in ("name", "email", "phone", "company"):
            val = data.get(key)
            if val and str(val).lower() not in ("null", "none", ""):
                regex_result[key] = regex_result[key] or (
                    str(val).lower() if key == "email" else str(val).strip().title() if key == "name" else str(val).strip()
                )
    except Exception as e:
        print(f"Groq customer extraction error: {e}")

    if regex_result.get("phone"):
        digits = re.sub(r'\D', '', regex_result["phone"])
        if len(digits) >= 10:
            regex_result["phone"] = digits[-10:]

    return regex_result
