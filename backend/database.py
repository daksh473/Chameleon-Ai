import sqlite3
import json
from datetime import datetime

DB_PATH = "smartcare.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            issue TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT NOT NULL,
            created_at TEXT NOT NULL,
            resolved_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            sentiment_score REAL NOT NULL,
            emotion TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            language TEXT DEFAULT 'en'
        )
    ''')

    try:
        cursor.execute("ALTER TABLE knowledge_base ADD COLUMN language TEXT DEFAULT 'en'")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            language TEXT,
            confidence REAL,
            timestamp TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            sender TEXT,
            subject TEXT,
            body TEXT,
            sentiment_score REAL,
            emotion TEXT,
            action TEXT,
            ticket_id INTEGER,
            reply_sent TEXT,
            reply_sent_at TEXT,
            received_at TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            company TEXT,
            source TEXT,
            status TEXT DEFAULT 'lead',
            risk_score REAL DEFAULT 0.5,
            total_conversations INTEGER DEFAULT 0,
            avg_sentiment REAL DEFAULT 0.5,
            total_tickets INTEGER DEFAULT 0,
            revenue_generated REAL DEFAULT 0,
            created_at TEXT,
            last_contact TEXT,
            notes TEXT,
            tags TEXT
        )
    ''')

    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN tags TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE customers ADD COLUMN session_id TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE conversations ADD COLUMN language TEXT DEFAULT 'en'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE conversations ADD COLUMN channel TEXT DEFAULT 'dashboard'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE tickets ADD COLUMN language TEXT DEFAULT 'en'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE tickets ADD COLUMN source TEXT DEFAULT 'dashboard'")
    except sqlite3.OperationalError:
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            title TEXT,
            value REAL,
            stage TEXT,
            probability INTEGER,
            expected_close TEXT,
            created_at TEXT,
            updated_at TEXT,
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            deal_id INTEGER,
            type TEXT,
            description TEXT,
            sentiment_score REAL,
            created_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            status TEXT DEFAULT 'online',
            current_conversations INTEGER DEFAULT 0,
            max_conversations INTEGER DEFAULT 3,
            specialization TEXT DEFAULT 'general',
            avg_rating REAL DEFAULT 5.0,
            total_handled INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS handoffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            customer_id INTEGER,
            agent_id INTEGER,
            reason TEXT,
            sentiment_score REAL,
            emotion TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            conversation_history TEXT,
            agent_notes TEXT,
            created_at TEXT,
            accepted_at TEXT,
            resolved_at TEXT,
            customer_rating INTEGER,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            customer_identifier TEXT,
            memory_type TEXT,
            key TEXT,
            value TEXT,
            importance REAL DEFAULT 0.5,
            created_at TEXT,
            last_accessed TEXT,
            access_count INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_identifier TEXT UNIQUE,
            summary TEXT,
            total_conversations INTEGER,
            common_issues TEXT,
            personality_traits TEXT,
            preferred_language TEXT,
            sentiment_trend TEXT,
            last_updated TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL,
            calculated_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS import_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            detected_type TEXT,
            total_rows INTEGER DEFAULT 0,
            imported INTEGER DEFAULT 0,
            skipped INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            status TEXT DEFAULT 'completed',
            imported_ids TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS excel_sync_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_type TEXT NOT NULL,
            source_url TEXT,
            source_path TEXT,
            status TEXT DEFAULT 'disconnected',
            last_synced TEXT,
            auto_sync INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')

    # Seed Agents
    cursor.execute('SELECT COUNT(*) FROM agents')
    if cursor.fetchone()[0] == 0:
        agents_data = [
            ("Rahul Sharma", "rahul@smartcare.ai", "online", "billing", datetime.now().isoformat()),
            ("Priya Singh", "priya@smartcare.ai", "online", "technical", datetime.now().isoformat()),
            ("Amit Kumar", "amit@smartcare.ai", "busy", "general", datetime.now().isoformat())
        ]
        cursor.executemany('INSERT INTO agents (name, email, status, specialization, created_at) VALUES (?, ?, ?, ?, ?)', agents_data)

    # Seed Knowledge Base
    cursor.execute('SELECT COUNT(*) FROM knowledge_base')
    if cursor.fetchone()[0] == 0:
        faqs = [
            ("What are your shipping times?", "Standard shipping takes 3-5 business days. Expedited takes 1-2 business days.", "shipping"),
            ("Do you ship internationally?", "Yes, we ship to over 50 countries globally. International shipping takes 7-14 days.", "shipping"),
            ("How do I return a product?", "You can return any unused product within 30 days of receipt. Visit your account to print a return label.", "refund"),
            ("When will I get my refund?", "Refunds are processed within 3-5 business days after we receive the returned item.", "refund"),
            ("How do I reset my password?", "Click 'Forgot Password' on the login screen. We will send a reset link to your registered email.", "account"),
            ("Can I change my email address?", "Yes, go to Account Settings > Profile to update your email address.", "account"),
            ("Are your products vegan?", "Yes, all our products are 100% vegan and cruelty-free.", "product"),
            ("Do you offer samples?", "We include 2 free samples with every order above $50.", "product"),
            ("What payment methods do you accept?", "We accept Visa, Mastercard, American Express, PayPal, and Apple Pay.", "payment"),
            ("Why was my card declined?", "Please check your billing address and CVV. If the problem persists, contact your bank.", "payment")
        ]
        cursor.executemany('INSERT INTO knowledge_base (question, answer, category, usage_count) VALUES (?, ?, ?, 0)', faqs)
        
    conn.commit()
    conn.close()

# -----------------
# TICKETS FUNCTIONS
# -----------------
def create_ticket(customer_name: str, issue: str, score: float, language: str = "en", source: str = "dashboard"):
    priority = "LOW"
    if score < 0.3:
        priority = "HIGH"
    elif score <= 0.7:
        priority = "MEDIUM"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tickets (customer_name, issue, status, priority, created_at, language, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (customer_name, issue, "OPEN", priority, datetime.now().isoformat(), language, source))
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_ticket(ticket_id)

def get_all_tickets():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_ticket(ticket_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def resolve_ticket(ticket_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tickets SET status = "RESOLVED", resolved_at = ? WHERE id = ?
    ''', (datetime.now().isoformat(), ticket_id))
    conn.commit()
    conn.close()
    return get_ticket(ticket_id)

def get_tickets_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tickets')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = "OPEN"')
    open_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = "RESOLVED"')
    resolved_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM tickets WHERE priority = "HIGH"')
    high_priority = cursor.fetchone()[0]
    conn.close()
    return {
        "total": total,
        "open": open_count,
        "resolved": resolved_count,
        "high_priority": high_priority
    }

# -----------------------
# CONVERSATION FUNCTIONS
# -----------------------
def save_conversation_message(session_id: str, role: str, message: str, sentiment_score: float, emotion: str, action: str, language: str = "en", channel: str = "dashboard"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (session_id, role, message, sentiment_score, emotion, action, timestamp, language, channel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, role, message, sentiment_score, emotion, action, datetime.now().isoformat(), language, channel))
    conn.commit()
    conn.close()

# Legacy function for backward compatibility
def save_conversation(message: str, score: float, emotion: str, action: str, reply: str, channel: str = "dashboard"):
    save_conversation_message("legacy", "user", message, score, emotion, action, "en", channel)
    save_conversation_message("legacy", "assistant", reply, score, emotion, action, "en", channel)

def get_conversation_history(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp ASC', (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Legacy function for backward compatibility
def get_all_conversations():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Mock the old schema by fetching user messages and pairing them (not ideal, but serves legacy UI)
    cursor.execute('SELECT * FROM conversations WHERE role = "user" ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    
    legacy_format = []
    for r in rows:
        legacy_format.append({
            "id": r["id"],
            "message": r["message"],
            "score": r["sentiment_score"],
            "emotion": r["emotion"],
            "action": r["action"],
            "reply": "Reply via legacy", # Simplified for legacy
            "timestamp": r["timestamp"],
            "channel": r["channel"] if "channel" in r.keys() else "dashboard"
        })
    return legacy_format

# -------------------------
# KNOWLEDGE BASE FUNCTIONS
# -------------------------
def get_all_kb_entries():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM knowledge_base ORDER BY usage_count DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_kb_entry(question: str, answer: str, category: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO knowledge_base (question, answer, category, usage_count)
        VALUES (?, ?, ?, 0)
    ''', (question, answer, category))
    conn.commit()
    conn.close()

def increment_kb_usage(kb_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE knowledge_base SET usage_count = usage_count + 1 WHERE id = ?
    ''', (kb_id,))
    conn.commit()
    conn.close()

# -------------------------
# ANALYTICS FUNCTIONS
# -------------------------
def get_analytics_overview():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total conversations (user messages only)
    cursor.execute('SELECT COUNT(*) FROM conversations WHERE role = "user"')
    total_conversations = cursor.fetchone()[0]

    # Total tickets
    cursor.execute('SELECT COUNT(*) FROM tickets')
    total_tickets = cursor.fetchone()[0]

    # Resolution rate
    cursor.execute('SELECT COUNT(*) FROM tickets WHERE status = "RESOLVED"')
    resolved = cursor.fetchone()[0]
    resolution_rate = round((resolved / total_tickets * 100), 1) if total_tickets > 0 else 0.0

    # Avg sentiment
    cursor.execute('SELECT AVG(sentiment_score) FROM conversations WHERE role = "user"')
    avg_score_row = cursor.fetchone()[0]
    avg_sentiment_score = round(avg_score_row, 3) if avg_score_row else 0.0

    # Escalation rate
    cursor.execute('SELECT COUNT(*) FROM conversations WHERE role = "user" AND action = "ESCALATE"')
    escalations = cursor.fetchone()[0]
    escalation_rate = round((escalations / total_conversations * 100), 1) if total_conversations > 0 else 0.0

    # Upsell rate
    cursor.execute('SELECT COUNT(*) FROM conversations WHERE role = "user" AND action = "UPSELL"')
    upsells = cursor.fetchone()[0]
    upsell_rate = round((upsells / total_conversations * 100), 1) if total_conversations > 0 else 0.0

    # Busiest hour
    cursor.execute("""
        SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as cnt
        FROM conversations WHERE role = 'user'
        GROUP BY hour ORDER BY cnt DESC LIMIT 1
    """)
    busiest = cursor.fetchone()
    busiest_hour = busiest[0] if busiest else 0

    conn.close()
    return {
        "total_conversations": total_conversations,
        "total_tickets": total_tickets,
        "resolution_rate": resolution_rate,
        "avg_sentiment_score": avg_sentiment_score,
        "avg_response_time_ms": 950,  # Mocked — no real ms tracking in DB
        "escalation_rate": escalation_rate,
        "upsell_rate": upsell_rate,
        "busiest_hour": busiest_hour
    }

def get_sentiment_trend():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DATE(timestamp) as dt, AVG(sentiment_score) as avg_score, COUNT(*) as cnt
        FROM conversations WHERE role = 'user'
        AND DATE(timestamp) >= DATE('now', '-7 days')
        GROUP BY dt ORDER BY dt ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"date": r[0], "avg_score": round(r[1], 3), "count": r[2]} for r in rows]

def get_emotion_breakdown():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT emotion, COUNT(*) as cnt
        FROM conversations WHERE role = 'user'
        GROUP BY emotion ORDER BY cnt DESC
    """)
    rows = cursor.fetchall()
    total = sum(r[1] for r in rows)
    conn.close()
    return [
        {"emotion": r[0], "count": r[1], "percentage": round(r[1] / total * 100, 1) if total > 0 else 0}
        for r in rows
    ]

def get_action_distribution():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action, COUNT(*) as cnt
        FROM conversations WHERE role = 'user'
        GROUP BY action
    """)
    rows = cursor.fetchall()
    conn.close()
    result = {"ESCALATE": 0, "NORMAL": 0, "UPSELL": 0}
    for r in rows:
        if r[0] in result:
            result[r[0]] = r[1]
    return result

def get_hourly_activity():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as cnt
        FROM conversations WHERE role = 'user'
        AND DATE(timestamp) = DATE('now')
        GROUP BY hour ORDER BY hour ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"hour": r[0], "count": r[1]} for r in rows]

def get_all_ticket_issues():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT issue FROM tickets ORDER BY created_at DESC LIMIT 100')
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def save_voice_metadata(session_id: str, language: str, confidence: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO voice_metadata (session_id, language, confidence, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (session_id, language, confidence, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_voice_analytics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM voice_metadata')
    total_voice = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(confidence) FROM voice_metadata')
    avg_conf_row = cursor.fetchone()[0]
    avg_confidence = round(avg_conf_row, 3) if avg_conf_row else 0.0
    
    cursor.execute('''
        SELECT language, COUNT(*) as cnt FROM voice_metadata
        GROUP BY language ORDER BY cnt DESC LIMIT 1
    ''')
    lang_row = cursor.fetchone()
    most_common_lang = lang_row[0] if lang_row else "N/A"
    
    conn.close()
    return {
        "total_voice_conversations": total_voice,
        "most_common_language": most_common_lang,
        "avg_confidence_score": avg_confidence
    }

def save_email(message_id, sender, subject, body, score, emotion, action, ticket_id, received_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO emails (message_id, sender, subject, body, sentiment_score, emotion, action, ticket_id, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (message_id, sender, subject, body, score, emotion, action, ticket_id, received_at))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Already exists
    conn.close()

def get_all_emails():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM emails ORDER BY received_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_email_status(email_id, status, reply_sent, reply_sent_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE emails SET status = ?, reply_sent = ?, reply_sent_at = ? WHERE id = ?
    ''', (status, reply_sent, reply_sent_at, email_id))
    conn.commit()
    conn.close()

def get_email_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM emails')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM emails WHERE status = "pending"')
    pending = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM emails WHERE status = "replied"')
    replied = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM emails WHERE action = "ESCALATE"')
    escalated = cursor.fetchone()[0]
    cursor.execute('SELECT AVG(sentiment_score) FROM emails')
    avg_score = cursor.fetchone()[0]
    conn.close()
    return {
        "total_received": total,
        "pending": pending,
        "replied": replied,
        "escalated": escalated,
        "avg_sentiment": round(avg_score, 3) if avg_score else 0.0
    }

# ==========================================
# CRM DATABASE FUNCTIONS
# ==========================================

def get_customers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM customers ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_customer(customer_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_customer_full_profile(customer_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
    customer_row = cursor.fetchone()
    if not customer_row:
        conn.close()
        return None
        
    customer = dict(customer_row)
    
    # Timeline
    cursor.execute('SELECT * FROM activities WHERE customer_id = ? ORDER BY created_at DESC', (customer_id,))
    timeline = [dict(r) for r in cursor.fetchall()]
    
    # Deals
    cursor.execute('SELECT * FROM deals WHERE customer_id = ? ORDER BY created_at DESC', (customer_id,))
    deals = [dict(r) for r in cursor.fetchall()]
    
    # Emails
    emails = []
    tickets = []
    
    if customer.get('email'):
        cursor.execute('SELECT * FROM emails WHERE sender LIKE ? ORDER BY received_at DESC', (f"%{customer['email']}%",))
        emails = [dict(r) for r in cursor.fetchall()]
        
    if customer.get('name'):
        cursor.execute('SELECT * FROM tickets WHERE customer_name = ? ORDER BY created_at DESC', (customer['name'],))
        tickets = [dict(r) for r in cursor.fetchall()]
        
    conn.close()
    
    # Merge activities with emails and tickets for a master timeline
    master_timeline = timeline.copy()
    
    for em in emails:
        master_timeline.append({
            "type": "email",
            "description": f"Email: {em['subject']}",
            "sentiment_score": em['sentiment_score'],
            "created_at": em['received_at']
        })
        
    for tk in tickets:
        master_timeline.append({
            "type": "ticket",
            "description": f"Ticket #{tk['id']} - {tk['issue']}",
            "sentiment_score": None, # or sentiment logic
            "created_at": tk['created_at']
        })
        
    # Sort descending
    master_timeline.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Sentiment trend: last 10 interactions with valid sentiment
    sentiment_trend = [t for t in master_timeline if t.get('sentiment_score') is not None][:10]
    sentiment_trend.reverse() # chronological order for charting
    
    # Interactions count
    total_interactions = len(master_timeline)
    
    # User requested flat structure with defaults
    response = dict(customer)
    response["id"] = customer.get("id", customer_id)
    response["name"] = customer.get("name", "Unknown")
    response["email"] = customer.get("email", "")
    response["status"] = customer.get("status") or "lead"
    response["risk_score"] = customer.get("risk_score") if customer.get("risk_score") is not None else 0.5
    response["avg_sentiment"] = customer.get("avg_sentiment") if customer.get("avg_sentiment") is not None else 0.5
    response["total_conversations"] = total_interactions
    response["total_tickets"] = len(tickets)
    response["activities"] = master_timeline
    response["deals"] = deals
    response["sentiment_trend"] = sentiment_trend
    response["notes"] = customer.get("notes") or ""
    
    # Original nested structure for the 3-column UI
    response["profile"] = customer
    response["timeline"] = master_timeline
    response["emails"] = emails
    response["tickets"] = tickets
    response["total_interactions"] = total_interactions
    
    return response

def create_customer(name, email, phone, company, source, notes, session_id=None):
    from datetime import datetime
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO customers (name, email, phone, company, source, status, created_at, last_contact, notes, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, company, source, "lead", now, now, notes, session_id))
        conn.commit()
        customer_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        if email:
            cursor.execute('SELECT id FROM customers WHERE email = ?', (email,))
            row = cursor.fetchone()
            customer_id = row[0] if row else None
        else:
            customer_id = None
        conn.commit()
    conn.close()
    return customer_id

def find_customer_for_chat(session_id=None, email=None, name=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if session_id:
        cursor.execute('SELECT * FROM customers WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    if email:
        cursor.execute('SELECT * FROM customers WHERE LOWER(email) = LOWER(?)', (email,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    if name and name.lower() not in ("chat user", "unknown"):
        cursor.execute('SELECT * FROM customers WHERE LOWER(name) = LOWER(?)', (name,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    conn.close()
    return None

def upsert_customer_from_chat(session_id: str, extracted: dict, sentiment_score: float = None, message_snippet: str = ""):
    """Create or update a CRM customer from dashboard chat."""
    from datetime import datetime
    now = datetime.now().isoformat()

    name = extracted.get("name") or None
    email = extracted.get("email") or None
    phone = extracted.get("phone") or None
    company = extracted.get("company") or None

    existing = find_customer_for_chat(
        session_id=session_id,
        email=email,
        name=name
    )

    if existing:
        updates = {
            "last_contact": now,
            "total_conversations": (existing.get("total_conversations") or 0) + 1,
        }
        if name and name.lower() != "chat user":
            updates["name"] = name
        if email:
            updates["email"] = email
        if phone:
            updates["phone"] = phone
        if company:
            updates["company"] = company
        if session_id and not existing.get("session_id"):
            updates["session_id"] = session_id

        if sentiment_score is not None:
            prev_avg = existing.get("avg_sentiment") or 0.5
            total = existing.get("total_conversations") or 0
            new_avg = ((prev_avg * total) + sentiment_score) / (total + 1)
            updates["avg_sentiment"] = round(new_avg, 3)

        update_customer(existing["id"], updates)
        desc = message_snippet[:120] if message_snippet else "Dashboard chat message"
        log_activity(existing["id"], "chat", desc, sentiment_score)
        return {"customer_id": existing["id"], "created": False, "name": updates.get("name", existing["name"])}

    display_name = name or "Chat User"
    cid = create_customer(
        name=display_name,
        email=email,
        phone=phone,
        company=company,
        source="chat",
        notes=f"Auto-created from dashboard chat session {session_id[:8]}",
        session_id=session_id
    )
    if cid and sentiment_score is not None:
        update_customer(cid, {"avg_sentiment": sentiment_score})

    if cid:
        log_activity(cid, "chat", message_snippet[:120] if message_snippet else "Started dashboard chat", sentiment_score)
        log_activity(cid, "note", "Customer profile auto-created from chat")

    return {"customer_id": cid, "created": True, "name": display_name}

def update_customer(customer_id, data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in data.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(customer_id)
    cursor.execute(f'''
        UPDATE customers SET {', '.join(fields)} WHERE id = ?
    ''', tuple(values))
    conn.commit()
    conn.close()

def delete_customer(customer_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
    cursor.execute('DELETE FROM activities WHERE customer_id = ?', (customer_id,))
    cursor.execute('DELETE FROM deals WHERE customer_id = ?', (customer_id,))
    conn.commit()
    conn.close()

def log_activity(customer_id, type_str, description, sentiment_score=None, deal_id=None):
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO activities (customer_id, deal_id, type, description, sentiment_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (customer_id, deal_id, type_str, description, sentiment_score, datetime.now().isoformat()))
    
    # Update customer last_contact and re-calculate averages
    cursor.execute('SELECT AVG(sentiment_score), COUNT(*) FROM activities WHERE customer_id = ? AND sentiment_score IS NOT NULL', (customer_id,))
    res = cursor.fetchone()
    avg_sent = res[0] or 0.5
    total_convs = res[1] or 0
    
    cursor.execute('''
        UPDATE customers 
        SET last_contact = ?, avg_sentiment = ?, total_conversations = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), avg_sent, total_convs, customer_id))
    
    conn.commit()
    conn.close()

def get_customer_timeline(customer_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM activities WHERE customer_id = ? ORDER BY created_at DESC', (customer_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_deal(customer_id, title, value, stage, probability, expected_close, notes):
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO deals (customer_id, title, value, stage, probability, expected_close, created_at, updated_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (customer_id, title, value, stage, probability, expected_close, now, now, notes))
    conn.commit()
    deal_id = cursor.lastrowid
    conn.close()
    return deal_id

def get_deals():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.*, c.name as customer_name 
        FROM deals d 
        LEFT JOIN customers c ON d.customer_id = c.id
        ORDER BY d.created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_deal(deal_id, data):
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in data.items():
        fields.append(f"{k} = ?")
        values.append(v)
    
    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    
    values.append(deal_id)
    cursor.execute(f'''
        UPDATE deals SET {', '.join(fields)} WHERE id = ?
    ''', tuple(values))
    conn.commit()
    conn.close()

def delete_deal(deal_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM deals WHERE id = ?', (deal_id,))
    conn.commit()
    conn.close()

def get_crm_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM customers')
    total_customers = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM customers WHERE risk_score < 0.3')
    at_risk_customers = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(value) FROM deals')
    total_deals_value = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT SUM(value) FROM deals WHERE stage = "won"')
    won_deals_value = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM deals WHERE stage = "won"')
    won_count = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM deals')
    total_deals = cursor.fetchone()[0] or 0
    
    conversion_rate = (won_count / total_deals * 100) if total_deals > 0 else 0
    
    from datetime import datetime, timedelta
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    cursor.execute('SELECT COUNT(*) FROM customers WHERE created_at > ?', (thirty_days_ago,))
    new_this_month = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_customers": total_customers,
        "new_this_month": new_this_month,
        "total_deals_value": total_deals_value,
        "won_deals_value": won_deals_value,
        "conversion_rate": round(conversion_rate, 1),
        "at_risk_customers": at_risk_customers
    }

# -----------------
# AGENT & HANDOFF FUNCTIONS
# -----------------
def get_agents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agents')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_agent(agent_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_agent(name, email, specialization="general", max_conversations=3):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        from datetime import datetime
        cursor.execute('''
            INSERT INTO agents (name, email, specialization, max_conversations, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, specialization, max_conversations, datetime.now().isoformat()))
        conn.commit()
        aid = cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute('SELECT id FROM agents WHERE email = ?', (email,))
        aid = cursor.fetchone()[0]
    conn.close()
    return aid

def update_agent_status(agent_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE agents SET status = ? WHERE id = ?', (status, agent_id))
    conn.commit()
    conn.close()
    return get_agent(agent_id)

def create_handoff(session_id, customer_id, agent_id, reason, sentiment_score, emotion, priority, conversation_history):
    from datetime import datetime
    import json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO handoffs (session_id, customer_id, agent_id, reason, sentiment_score, emotion, priority, conversation_history, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, customer_id, agent_id, reason, sentiment_score, emotion, priority, json.dumps(conversation_history), datetime.now().isoformat()))
    conn.commit()
    hid = cursor.lastrowid
    conn.close()
    return hid

def get_handoffs(status=None, agent_id=None):
    import json
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = 'SELECT h.*, c.name as customer_name, a.name as agent_name FROM handoffs h LEFT JOIN customers c ON h.customer_id = c.id LEFT JOIN agents a ON h.agent_id = a.id WHERE 1=1'
    params = []
    if status:
        query += ' AND h.status = ?'
        params.append(status)
    if agent_id:
        query += ' AND h.agent_id = ?'
        params.append(agent_id)
    query += ' ORDER BY h.created_at DESC'
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d['conversation_history'] = json.loads(d['conversation_history']) if d['conversation_history'] else []
        result.append(d)
    return result

def accept_handoff(handoff_id):
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE handoffs SET status = "active", accepted_at = ? WHERE id = ?', (datetime.now().isoformat(), handoff_id))
    cursor.execute('SELECT agent_id FROM handoffs WHERE id = ?', (handoff_id,))
    agent_id = cursor.fetchone()[0]
    if agent_id:
        cursor.execute('UPDATE agents SET current_conversations = current_conversations + 1 WHERE id = ?', (agent_id,))
    conn.commit()
    conn.close()

def resolve_handoff(handoff_id, resolution_notes, customer_rating):
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE handoffs SET status = "resolved", resolved_at = ?, agent_notes = ?, customer_rating = ? WHERE id = ?
    ''', (datetime.now().isoformat(), resolution_notes, customer_rating, handoff_id))
    cursor.execute('SELECT agent_id FROM handoffs WHERE id = ?', (handoff_id,))
    agent_id = cursor.fetchone()[0]
    if agent_id:
        cursor.execute('UPDATE agents SET current_conversations = MAX(0, current_conversations - 1), total_handled = total_handled + 1 WHERE id = ?', (agent_id,))
        # Update agent rating
        cursor.execute('SELECT avg_rating, total_handled FROM agents WHERE id = ?', (agent_id,))
        row = cursor.fetchone()
        if row and customer_rating:
            curr_rating = row[0]
            total = row[1]
            new_avg = ((curr_rating * (total - 1)) + customer_rating) / total
            cursor.execute('UPDATE agents SET avg_rating = ? WHERE id = ?', (new_avg, agent_id))
    conn.commit()
    conn.close()

def transfer_handoff(handoff_id, new_agent_id, reason):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Decrement old agent
    cursor.execute('SELECT agent_id FROM handoffs WHERE id = ?', (handoff_id,))
    old_agent_id = cursor.fetchone()[0]
    if old_agent_id:
        cursor.execute('UPDATE agents SET current_conversations = MAX(0, current_conversations - 1) WHERE id = ?', (old_agent_id,))
    # Update handoff
    cursor.execute('''
        UPDATE handoffs SET agent_id = ?, reason = reason || ' | Transfer: ' || ?, status = "pending" WHERE id = ?
    ''', (new_agent_id, reason, handoff_id))
    conn.commit()
    conn.close()

# -----------------
# MEMORY FUNCTIONS
# -----------------
def store_memory(session_id: str, customer_identifier: str, memory_type: str, key: str, value: str, importance: float = 0.5):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM memory_store
        WHERE customer_identifier = ? AND memory_type = ? AND key = ?
    ''', (customer_identifier, memory_type, key))
    existing = cursor.fetchone()
    if existing:
        cursor.execute('''
            UPDATE memory_store SET value = ?, importance = ?, last_accessed = ?, access_count = access_count + 1
            WHERE id = ?
        ''', (value, importance, now, existing[0]))
        mem_id = existing[0]
    else:
        cursor.execute('''
            INSERT INTO memory_store (session_id, customer_identifier, memory_type, key, value, importance, created_at, last_accessed, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (session_id, customer_identifier, memory_type, key, value, importance, now, now))
        mem_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_memory_by_id(mem_id)

def get_memory_by_id(mem_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM memory_store WHERE id = ?', (mem_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_memories_for_customer(customer_identifier: str, limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        UPDATE memory_store SET last_accessed = ?, access_count = access_count + 1
        WHERE customer_identifier = ?
    ''', (now, customer_identifier))
    cursor.execute('''
        SELECT * FROM memory_store WHERE customer_identifier = ?
        ORDER BY importance DESC, last_accessed DESC LIMIT ?
    ''', (customer_identifier, limit))
    rows = cursor.fetchall()
    conn.commit()
    conn.close()
    return [dict(r) for r in rows]

def get_memory_count(customer_identifier: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM memory_store WHERE customer_identifier = ?', (customer_identifier,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def save_conversation_summary(customer_identifier: str, summary: str, total_conversations: int,
                               common_issues: list, personality_traits: dict, preferred_language: str,
                               sentiment_trend: str):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversation_summaries
        (customer_identifier, summary, total_conversations, common_issues, personality_traits, preferred_language, sentiment_trend, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(customer_identifier) DO UPDATE SET
            summary = excluded.summary,
            total_conversations = excluded.total_conversations,
            common_issues = excluded.common_issues,
            personality_traits = excluded.personality_traits,
            preferred_language = excluded.preferred_language,
            sentiment_trend = excluded.sentiment_trend,
            last_updated = excluded.last_updated
    ''', (customer_identifier, summary, total_conversations, json.dumps(common_issues),
          json.dumps(personality_traits), preferred_language, sentiment_trend, now))
    conn.commit()
    conn.close()
    return get_conversation_summary(customer_identifier)

def get_conversation_summary(customer_identifier: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM conversation_summaries WHERE customer_identifier = ?', (customer_identifier,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d['common_issues'] = json.loads(d['common_issues']) if d['common_issues'] else []
    d['personality_traits'] = json.loads(d['personality_traits']) if d['personality_traits'] else {}
    return d

def get_open_ticket_count_for_customer(customer_name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tickets WHERE customer_name LIKE ? AND status = "OPEN"', (f'%{customer_name}%',))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def create_voice_ticket(customer_name: str, transcript: str, score: float, emotion: str, audio_duration: float, language: str = "en"):
    issue = (
        f"[Voice Message] Transcript: {transcript} | "
        f"Sentiment: {score:.2f} | Emotion: {emotion} | "
        f"Duration: {audio_duration:.1f}s"
    )
    return create_ticket(customer_name, issue, score, language)

def backfill_memories_from_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM memory_store')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return {"backfilled": 0, "reason": "memory already populated"}

    count = 0
    now = datetime.now().isoformat()

    cursor.execute('SELECT * FROM tickets ORDER BY created_at ASC')
    for t in cursor.fetchall():
        cid = t['customer_name']
        cursor.execute('''
            INSERT INTO memory_store (session_id, customer_identifier, memory_type, key, value, importance, created_at, last_accessed, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (None, cid, 'complaint', f"ticket_{t['id']}", t['issue'], 0.8 if t['priority'] == 'HIGH' else 0.6, t['created_at'], now))
        count += 1

    cursor.execute('SELECT * FROM emails ORDER BY received_at ASC')
    for e in cursor.fetchall():
        cid = e['sender'] or 'unknown_email'
        cursor.execute('''
            INSERT INTO memory_store (session_id, customer_identifier, memory_type, key, value, importance, created_at, last_accessed, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (None, cid, 'context', f"email_{e['id']}", f"{e['subject']}: {(e['body'] or '')[:200]}", 0.5, e['received_at'] or now, now))
        count += 1

    conn.close()

    conn2 = sqlite3.connect(DB_PATH)
    cursor2 = conn2.cursor()
    cursor2.execute('SELECT DISTINCT session_id FROM conversations')
    sessions = [r[0] for r in cursor2.fetchall()]
    conn2.close()

    for sid in sessions:
        history = get_conversation_history(sid)
        for msg in history:
            if msg['role'] == 'user' and len(msg['message']) > 10:
                store_memory(sid, sid, 'context', f"msg_{msg['id']}", msg['message'][:300], 0.4)
                count += 1

    return {"backfilled": count}

# -----------------
# PREDICTIONS CACHE & DATA
# -----------------
CACHE_TTL_SECONDS = 3600

def get_predictions_cache(cache_key: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM predictions_cache WHERE cache_key = ?', (cache_key,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    from datetime import datetime
    calculated = datetime.fromisoformat(row['calculated_at'])
    age = (datetime.now() - calculated).total_seconds()
    return {
        "data": json.loads(row['data']),
        "calculated_at": row['calculated_at'],
        "age_seconds": age,
        "expired": age >= CACHE_TTL_SECONDS
    }

def set_predictions_cache(cache_key: str, data: dict):
    from datetime import datetime
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions_cache (cache_key, data, calculated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET data = excluded.data, calculated_at = excluded.calculated_at
    ''', (cache_key, json.dumps(data), now))
    conn.commit()
    conn.close()

def get_conversations_since(days: int = 30):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT session_id, message, sentiment_score, emotion, action, timestamp
        FROM conversations WHERE role = 'user'
        AND timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
    ''', (f'-{days} days',))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_tickets_since(days: int = 90):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tickets WHERE created_at >= datetime('now', ?)
        ORDER BY created_at ASC
    ''', (f'-{days} days',))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_open_tickets_for_customer(customer_name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM tickets
        WHERE status = 'OPEN' AND customer_name LIKE ?
    ''', (f'%{customer_name}%',))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_ticket_weekday_distribution(days: int = 90):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT CAST(strftime('%w', created_at) AS INTEGER) as dow, COUNT(*) as cnt
        FROM tickets WHERE created_at >= datetime('now', ?)
        GROUP BY dow
    ''', (f'-{days} days',))
    rows = cursor.fetchall()
    conn.close()
    dist = {i: 0 for i in range(7)}
    for dow, cnt in rows:
        dist[dow] = cnt
    return dist

def get_daily_ticket_counts(days: int = 30):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DATE(created_at) as dt, COUNT(*) as cnt
        FROM tickets WHERE created_at >= datetime('now', ?)
        GROUP BY dt ORDER BY dt
    ''', (f'-{days} days',))
    rows = cursor.fetchall()
    conn.close()
    return [{"date": r[0], "count": r[1]} for r in rows]

def get_daily_sentiment(days: int = 30):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DATE(timestamp) as dt, AVG(sentiment_score) as avg_score, COUNT(*) as cnt
        FROM conversations WHERE role = 'user'
        AND timestamp >= datetime('now', ?)
        GROUP BY dt ORDER BY dt
    ''', (f'-{days} days',))
    rows = cursor.fetchall()
    conn.close()
    return [{"date": r[0], "avg_score": round(r[1], 3) if r[1] else 0.5, "count": r[2]} for r in rows]

def get_customer_activity_hours(customer_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT CAST(strftime('%w', created_at) AS INTEGER) as dow,
               CAST(strftime('%H', created_at) AS INTEGER) as hour,
               COUNT(*) as cnt
        FROM activities WHERE customer_id = ?
        GROUP BY dow, hour ORDER BY cnt DESC
    ''', (customer_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"dow": r[0], "hour": r[1], "count": r[2]} for r in rows]

def match_customer_conversations(customer, conversations):
    """Match conversations to a customer by session_id, name, or email."""
    sid = customer.get('session_id') or ''
    name = (customer.get('name') or '').lower()
    email = (customer.get('email') or '').lower()
    matched = []
    for c in conversations:
        session = c.get('session_id', '')
        msg = (c.get('message') or '').lower()
        if sid and session == sid:
            matched.append(c)
        elif name and name not in ('chat user', 'unknown') and name in msg:
            matched.append(c)
        elif email and email in msg:
            matched.append(c)
        elif name and name not in ('chat user', 'unknown') and name in (c.get('customer_name') or '').lower():
            matched.append(c)
    return matched