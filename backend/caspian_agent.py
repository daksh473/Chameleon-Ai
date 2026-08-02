import os
from ai.sentiment_classifier import analyze_sentiment, decide_action
from ai.bot_reply import generate_reply
from database import save_conversation, create_ticket
from caspian_sdk import CommClient
from dotenv import load_dotenv

load_dotenv()

client = CommClient()

@client.on_message
def handle_message(message):
    text = message.text
    channel = message.channel  # e.g. "email" or "telegram"
    sender = message.sender    # customer identifier from that channel

    # Reuse existing pipeline exactly as Live Chat does
    result = analyze_sentiment(text)
    action = decide_action(result["score"])
    
    # We pass empty history and memory for now, matching the simplified usage pattern 
    # Or we can just use generate_reply(text, action, [], "", "en") since main.py passes 5 args
    reply_text = generate_reply(text, action, [], "", "en")

    # Save to the same conversations table used everywhere else,
    # tagging the channel so we know it came from Caspian
    save_conversation(
        message=text,
        score=result["score"],
        emotion=result["emotion"],
        action=action,
        reply=reply_text,
        channel=f"caspian-{channel}"
    )

    # If escalated, also auto-create a ticket exactly like existing logic does
    if action == "ESCALATE":
        create_ticket(
            customer_name=sender,
            issue=text,
            score=result["score"],
            language="en",
            source=f"caspian-{channel}"
        )

    # Reply back on the SAME channel automatically, threaded correctly
    message.reply(reply_text)

def start_caspian_listener():
    # Will connect to email and telegram if the CASPIAN_API_KEY is present
    client.listen()
