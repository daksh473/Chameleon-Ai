import traceback
from database import get_handoff, save_conversation_message

def send_agent_message(handoff_id: int, text: str) -> dict:
    """
    Sends an agent's message to the customer on whichever channel 
    they're on, and returns a result dict indicating success/failure 
    per channel, with the raw provider response for debugging.
    """
    handoff = get_handoff(handoff_id)
    if not handoff:
        return {"success": False, "error": "Handoff not found"}
        
    channel = handoff["channel"]
    sender_id = handoff["sender_id"]
    
    result = {"success": False, "error": "Unknown channel"}
    
    try:
        if channel in ("telegram", "caspian-telegram"):
            from caspian_agent import client
            print(f"Sending message via Caspian SDK to {sender_id} on {channel}...")
            # Use the Caspian SDK's method for sending a NEW outbound message
            api_result = client.send_message(conversation_id=sender_id, text=text)
            print(f"Caspian SDK response: {api_result}")
            result = {"success": True, "provider_response": api_result}
            
        elif channel in ("email", "caspian-email"):
            import smtplib
            from email.message import EmailMessage
            try:
                from routers.email import EMAIL_USER, EMAIL_PASSWORD
            except ImportError:
                import os
                EMAIL_USER = os.environ.get("EMAIL_USER")
                EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
                
            print(f"Sending SMTP email to {sender_id}...")
            msg = EmailMessage()
            msg.set_content(text)
            msg['Subject'] = "Follow-up from Chameleon AI Support"
            msg['From'] = EMAIL_USER
            msg['To'] = sender_id
            
            # This will fail locally if credentials aren't set, but it proves the code path
            if EMAIL_USER and EMAIL_PASSWORD:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(EMAIL_USER, EMAIL_PASSWORD)
                    smtp.send_message(msg)
                result = {"success": True, "provider_response": "Email sent via SMTP"}
            else:
                result = {"success": False, "error": "SMTP credentials not configured"}
            
        elif channel == "live_chat":
            import main
            print(f"Pushing message to Live Chat session {handoff['session_id']}...")
            payload = {
                "type": "agent_reply",
                "message": text
            }
            # Broadcast to customer websocket
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(main.manager.broadcast_to_session(handoff["session_id"], payload))
            except RuntimeError:
                asyncio.run(main.manager.broadcast_to_session(handoff["session_id"], payload))
            
            result = {"success": True, "provider_response": "WebSocket pushed"}
            
        else:
            result = {"success": False, "error": f"Unsupported channel: {channel}"}
            
    except Exception as e:
        print(f"Failed to send outbound message: {e}")
        traceback.print_exc()
        result = {"success": False, "error": str(e), "traceback": traceback.format_exc()}

    # Save to conversation history using the unified schema
    if result["success"]:
        save_conversation_message(
            handoff_id=handoff_id,
            sender_type="agent",
            text=text,
            channel=channel
        )

    return result
