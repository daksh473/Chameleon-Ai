from groq import Groq
import os
from dotenv import load_dotenv
from typing import List, Dict
from ai.knowledge_ai import search_knowledge_base

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPTS = {
    "ESCALATE": """You are a empathetic customer service bot. 
The customer is angry or frustrated. 
Apologize sincerely, acknowledge their problem, and tell them a human agent will help them shortly and a ticket has been auto-created.
Keep it under 2 sentences.""",

    "NORMAL": """You are a helpful customer service bot.
The customer has a normal query.
Answer helpfully and professionally using the conversation context if needed.
Keep it under 2 sentences.""",

    "UPSELL": """You are a friendly sales bot.
The customer is happy and satisfied.
Thank them warmly and offer them a special discount or upgrade.
Keep it under 2 sentences."""
}

def generate_reply(message: str, action: str, history: List[Dict[str, str]] = None, memory_context: str = None, detected_language: str = "en") -> dict:
    print(f"Checking knowledge base for: {message}")
    kb_result = search_knowledge_base(message)
    if kb_result["source"] == "knowledge_base":
        print(f"Knowledge Base match found (confidence {kb_result['confidence']}): {kb_result['answer']}")
        return kb_result

    print("No Knowledge Base match found. Falling back to AI generated response.")
    prompt = PROMPTS.get(action, PROMPTS["NORMAL"])
    
    # Append the language override directly
    prompt += f"\n\nReply in {detected_language} language only. Use the same script (Devanagari/Tamil/Bengali etc.) as the customer."
    
    if memory_context:
        prompt += f"\n\nCustomer Context:\n{memory_context}"
    
    messages = [{"role": "system", "content": prompt}]
    
    if history:
        # history structure: [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
        # Take up to last 10 messages for context
        messages.extend(history[-10:])
        
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=150,
        temperature=0.7
    )
    return {
        "source": "ai_generated",
        "answer": response.choices[0].message.content.strip(),
        "confidence": kb_result.get("confidence", 0.0)
    }

# Test
if __name__ == "__main__":
    tests = [
        ("Yeh bakwaas service hai!", "ESCALATE"),
        ("Mera order status kya hai?", "NORMAL"),
        ("Bahut acha service hai shukriya!", "UPSELL"),
    ]
    for msg, action in tests:
        reply = generate_reply(msg, action)
        print(f"\n[{action}] Customer: {msg}")
        print(f"Bot [{reply['source']}]: {reply['answer']}")