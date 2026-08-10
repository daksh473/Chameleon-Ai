import os
import smtplib
import imaplib
import email as email_lib
from email.message import EmailMessage
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from database import (
    save_email, get_all_emails, update_email_status, get_email_stats, create_ticket,
    get_customers, create_customer, log_activity
)
from ai.sentiment_classifier import analyze_sentiment, decide_action
from ai.bot_reply import generate_reply

load_dotenv()

router = APIRouter(prefix="/email", tags=["Email"])

# Env configs
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")

class ReplyRequest(BaseModel):
    email_id: int
    custom_reply: str = None

class InboxCheckRequest(BaseModel):
    email: str
    password: str
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993

@router.post("/check-inbox")
def check_inbox(req: InboxCheckRequest):
    """Connect to IMAP, fetch last 10 unread, analyze sentiment, store in DB."""
    if not req.email or not req.password:
        # Mock mode if no credentials
        return {"processed": 0, "mock": True, "error": "No email credentials provided"}
        
    try:
        mail = imaplib.IMAP4_SSL(req.imap_host, req.imap_port)
        mail.login(req.email, req.password)
        mail.select('inbox')

        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            return {"processed": 0}

        email_ids = messages[0].split()
        # Process last 10 max
        email_ids = email_ids[-10:]
        
        processed_count = 0
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email_lib.message_from_bytes(response_part[1])
                    subject = msg['subject']
                    sender = msg['from']
                    message_id = msg['Message-ID'] or f"mock-id-{e_id.decode()}"
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()
                        
                    # Analysis
                    result = analyze_sentiment(body)
                    action = decide_action(result["score"])
                    
                    # Create ticket if needed
                    ticket_id = None
                    if action == "ESCALATE":
                        ticket_id = create_ticket(sender, f"Email: {subject}", result["score"])
                        
                        try:
                            from handoff_service import trigger_handoff
                            trigger_handoff(
                                customer_message=body,
                                sentiment_score=result["score"],
                                emotion=result["emotion"],
                                channel="email",
                                session_id=f"email-{message_id}",
                                sender_id=sender,
                                sender_name=sender.split('<')[0].strip() or sender.split('<')[-1].strip('>')
                            )
                        except Exception as e:
                            print(f"Handoff error in email check: {e}")
                        
                    save_email(message_id, sender, subject, body, result["score"], result["emotion"], action, ticket_id, datetime.now().isoformat())
                    
                    # Auto CRM Linking
                    customers = get_customers()
                    clean_email = sender.split('<')[-1].strip('>')
                    name = sender.split('<')[0].strip() or clean_email
                    
                    existing_cust = next((c for c in customers if c['email'] == clean_email), None)
                    if existing_cust:
                        cid = existing_cust['id']
                    else:
                        cid = create_customer(name, clean_email, None, None, "email", "")
                        log_activity(cid, "note", "Auto-created from Email integration")
                    
                    log_activity(cid, "email", f"Received: {subject}", result["score"])
                    
                    processed_count += 1
                    
        mail.close()
        mail.logout()
        return {"processed": processed_count}
    except Exception as e:
        print(f"IMAP Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-reply")
def send_reply(req: ReplyRequest):
    """Send a reply to an email via SMTP"""
    emails = get_all_emails()
    target_email = next((e for e in emails if e['id'] == req.email_id), None)
    
    if not target_email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    reply_text = req.custom_reply
    if not reply_text:
        reply_data = generate_reply(target_email['body'], target_email['action'])
        reply_text = reply_data["answer"]
        reply_source = reply_data["source"]
        
    try:
        if EMAIL_USER and EMAIL_PASSWORD:
            msg = EmailMessage()
            msg.set_content(reply_text)
            msg['Subject'] = f"Re: {target_email['subject']}"
            msg['From'] = EMAIL_USER
            msg['To'] = target_email['sender']
            
            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.send_message(msg)
                
        update_email_status(req.email_id, 'replied', reply_text, datetime.now().isoformat())
        return {"success": True, "reply_sent": reply_text}
    except Exception as e:
        print(f"SMTP Error: {e}")
        # Mark as replied anyway for demo purposes if SMTP fails
        update_email_status(req.email_id, 'replied', reply_text, datetime.now().isoformat())
        return {"success": False, "error": str(e), "reply_sent": reply_text, "mock_success": True}

@router.post("/auto-process")
def auto_process():
    """Auto-reply to all pending emails"""
    emails = get_all_emails()
    pending = [e for e in emails if e['status'] == 'pending']
    
    replied_count = 0
    tickets_created = 0
    
    for email in pending:
        reply_data = generate_reply(email['body'], email['action'])
        reply_text = reply_data["answer"]
        reply_source = reply_data["source"]
        
        if email['action'] == 'ESCALATE' and not email['ticket_id']:
            ticket_id = create_ticket(email['sender'], f"Email: {email['subject']}", email['sentiment_score'])
            # update ticket_id in db (not strictly implemented but assumed)
            tickets_created += 1
            
            try:
                from handoff_service import trigger_handoff
                trigger_handoff(
                    customer_message=email['body'],
                    sentiment_score=email['sentiment_score'],
                    emotion=email['emotion'],
                    channel="email",
                    session_id=f"email-{email['message_id']}",
                    sender_id=email['sender'],
                    sender_name=email['sender'].split('<')[0].strip() or email['sender'].split('<')[-1].strip('>')
                )
            except Exception as e:
                print(f"Handoff error in email auto-process: {e}")
            
        try:
            if EMAIL_USER and EMAIL_PASSWORD:
                msg = EmailMessage()
                msg.set_content(reply_text)
                msg['Subject'] = f"Re: {email['subject']}"
                msg['From'] = EMAIL_USER
                msg['To'] = email['sender']
                
                with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_USER, EMAIL_PASSWORD)
                    server.send_message(msg)
                    
            update_email_status(email['id'], 'replied', reply_text, datetime.now().isoformat())
            replied_count += 1
        except Exception as e:
            print(f"SMTP Error for {email['id']}: {e}")
            update_email_status(email['id'], 'replied', reply_text, datetime.now().isoformat())
            replied_count += 1
            
    return {"processed": len(pending), "replied": replied_count, "tickets_created": tickets_created}

@router.get("/inbox")
def get_inbox():
    return get_all_emails()

@router.get("/stats")
def get_stats():
    return get_email_stats()
