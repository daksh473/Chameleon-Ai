from fastapi import APIRouter
from pydantic import BaseModel
from database import get_all_kb_entries, add_kb_entry, increment_kb_usage
from groq import Groq
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

class AddKBRequest(BaseModel):
    question: str
    answer: str
    category: str

class SearchRequest(BaseModel):
    query: str

@router.post("/add")
def add_knowledge(req: AddKBRequest):
    add_kb_entry(req.question, req.answer, req.category)
    return {"message": "FAQ added successfully"}

@router.get("")
def get_knowledge():
    try:
        return get_all_kb_entries()
    except Exception as e:
        print(f"Failed to load knowledge base: {e}")
        return []

@router.post("/search")
def search_knowledge(req: SearchRequest):
    kb_entries = get_all_kb_entries()
    
    # Construct prompt for Groq to evaluate KB match or generate fresh answer
    kb_text = "\n".join([f"ID: {kb['id']} | Q: {kb['question']} | A: {kb['answer']}" for kb in kb_entries])
    
    prompt = f"""You are a helpful knowledge base assistant. 
Here are the existing FAQs:
{kb_text}

User Query: "{req.query}"

Task:
1. Determine if any existing FAQ answers the user's query well enough (confidence > 0.7).
2. If YES, return the ID of the FAQ, the original FAQ answer, and setting is_kb = true.
3. If NO, generate a fresh AI answer to the query, set kb_id to null, and setting is_kb = false.

Return STRICTLY a JSON object with this structure (no markdown formatting, just raw JSON):
{{
  "is_kb": boolean,
  "kb_id": int or null,
  "answer": "string"
}}
"""

    try:
        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group()
        result = json.loads(content)
        
        if result.get("is_kb") and result.get("kb_id"):
            increment_kb_usage(result["kb_id"])
            
        return result
    except Exception as e:
        # Fallback to pure AI if parsing fails
        print("Knowledge Search Error:", e)
        try:
            fallback_res = client.chat.completions.create(
                model="groq/compound-mini",
                messages=[{"role": "user", "content": req.query}],
                max_tokens=150,
                temperature=0.7
            )
            answer = fallback_res.choices[0].message.content.strip()
            answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
            return {
                "is_kb": False,
                "kb_id": None,
                "answer": answer
            }
        except Exception as fallback_e:
            print("Fallback Knowledge Search Error:", fallback_e)
            return {
                "is_kb": False,
                "kb_id": None,
                "answer": "Sorry, I am unable to answer your query right now due to a service error."
            }
