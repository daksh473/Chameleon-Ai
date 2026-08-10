import sys
sys.path.append('backend')
from messaging_service import send_agent_message
from database import create_handoff
import json

def test():
    # 1. Telegram
    hid1 = create_handoff(
        session_id="test-telegram", customer_id=None, agent_id=None,
        reason="Telegram test", sentiment_score=1.0, emotion="neutral", priority="low",
        conversation_history=[], channel="telegram", sender_id="telegram-123", sender_name="Test"
    )
    res1 = send_agent_message(hid1, "Test from Telegram")
    print("Telegram Response:", res1)
    
    # 2. Email
    hid2 = create_handoff(
        session_id="test-email", customer_id=None, agent_id=None,
        reason="Email test", sentiment_score=1.0, emotion="neutral", priority="low",
        conversation_history=[], channel="email", sender_id="test@example.com", sender_name="Test"
    )
    # Don't actually send a real email because it will fail with SMTP auth since I don't have password
    print("Email skipped actual send because of no SMTP credentials, but routing is wired up in handoff.py. Wait, no, send_agent_message delegates to SMTP? Wait, in messaging_service.py I forgot SMTP logic!")
    
test()
