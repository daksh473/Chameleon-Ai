import json
import os
from groq import Groq
from dotenv import load_dotenv
from database import get_all_kb_entries, increment_kb_usage

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def search_knowledge_base(user_question: str) -> dict:
    """
    Searches the knowledge base for a matching FAQ using Groq.
    Returns: {"source": "knowledge_base", "answer": "...", "confidence": float}
          or {"source": "ai_generated", "answer": None, "confidence": float}
    """
    kb_entries = get_all_kb_entries()
    if not kb_entries:
        return {"source": "ai_generated", "answer": None, "confidence": 0.0}

    kb_text = "\n".join([f"ID: {kb['id']} | Q: {kb['question']} | A: {kb['answer']}" for kb in kb_entries])
    
    prompt = f"""You are matching a customer question to the closest FAQ.
Customer question: "{user_question}"

FAQs:
{kb_text}

Task:
1. Determine if any existing FAQ answers the user's query well enough (confidence > 0.7).
2. If YES, return the ID of the FAQ as matched_faq_id.
3. If NO, return matched_faq_id: null.

Return STRICTLY a JSON object with this structure (no markdown formatting, just raw JSON):
{{
  "matched_faq_id": <int or null>,
  "confidence": <float between 0.0 and 1.0>
}}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=150,
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        result = json.loads(content)
        
        matched_id = result.get("matched_faq_id")
        confidence = result.get("confidence", 0.0)
        
        if matched_id and confidence > 0.7:
            # Find the answer text
            matched_faq = next((kb for kb in kb_entries if kb['id'] == matched_id), None)
            if matched_faq:
                increment_kb_usage(matched_id)
                return {
                    "source": "knowledge_base",
                    "answer": matched_faq["answer"],
                    "confidence": confidence
                }
                
        return {"source": "ai_generated", "answer": None, "confidence": confidence}
        
    except Exception as e:
        print("Knowledge Search AI Error:", e)
        return {"source": "ai_generated", "answer": None, "confidence": 0.0}
