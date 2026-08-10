import requests
import time
import sqlite3
import json

API_URL = "http://localhost:8000"

def run_test():
    print("=== End-to-End Handoff Test ===")
    
    # 1. Manually insert a mock telegram customer and handoff to simulate an escalated conversation
    conn = sqlite3.connect('backend/smartcare.db')
    cursor = conn.cursor()
    
    # Check if a test customer exists
    cursor.execute("SELECT id FROM customers WHERE name = 'Telegram Test User'")
    row = cursor.fetchone()
    if row:
        customer_id = row[0]
    else:
        cursor.execute("INSERT INTO customers (name, source) VALUES ('Telegram Test User', 'telegram')")
        customer_id = cursor.lastrowid
        conn.commit()
        
    # Clear phone number to test the "Add phone" flow
    cursor.execute("UPDATE customers SET phone = NULL WHERE id = ?", (customer_id,))
    
    # Create handoff
    cursor.execute("""
        INSERT INTO handoffs (customer_id, session_id, priority, reason, status, channel, sender_id, sender_name, created_at, conversation_history)
        VALUES (?, 'mock_session_tg_123', 'high', 'Test escalation', 'pending', 'telegram', '123456789', 'Telegram Test User', datetime('now'), ?)
    """, (customer_id, json.dumps([{"role": "user", "message": "I need a human now!"}])))
    handoff_id = cursor.lastrowid
    conn.commit()
    print(f"Created handoff {handoff_id} for customer {customer_id}")
    
    # 2. Accept handoff as agent 1
    res = requests.post(f"{API_URL}/handoff/accept/{handoff_id}?agent_id=1")
    print("Accept Handoff:", res.status_code)
    
    # 3. Send Agent Message
    print(f"\n[Test] Sending Direct Message on Telegram")
    res = requests.post(f"{API_URL}/handoff/agent-message/{handoff_id}", json={"message": "Hello from Agent Console!"})
    print("Agent Message Response:", res.status_code, res.text)
    
    # 4. Verify Call Customer fails without phone
    print(f"\n[Test] Attempting Call without Phone Number")
    res = requests.post(f"{API_URL}/handoff/call-customer/{handoff_id}")
    print("Call Response (Expected 400):", res.status_code, res.text)
    
    # 5. Add phone number
    print(f"\n[Test] Adding Phone Number inline")
    res = requests.post(f"{API_URL}/handoff/add-phone/{handoff_id}", json={"phone": "+1234567890"})
    print("Add Phone Response:", res.status_code, res.text)
    
    # 6. Call Customer with phone
    print(f"\n[Test] Attempting Call with Phone Number")
    res = requests.post(f"{API_URL}/handoff/call-customer/{handoff_id}")
    print("Call Response (Expected 200 Mock):", res.status_code, res.text)
    
    # Verify DB
    cursor.execute("SELECT * FROM calls WHERE handoff_id = ?", (handoff_id,))
    call_row = cursor.fetchone()
    print("\nCall logged in DB:", call_row)
    
    cursor.execute("SELECT conversation_history FROM handoffs WHERE id = ?", (handoff_id,))
    history = cursor.fetchone()[0]
    print("\nConversation history updated with agent message:", "Agent Console" in history)
    
    conn.close()

if __name__ == "__main__":
    run_test()
