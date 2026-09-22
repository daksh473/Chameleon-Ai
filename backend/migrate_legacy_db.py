import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smartcare.db")

def migrate_legacy_tables():
    if not os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check if customers.id is INTEGER
    c.execute("PRAGMA table_info(customers)")
    cust_cols = {row[1]: row[2] for row in c.fetchall()}
    if cust_cols.get("id", "").upper().startswith("INT"):
        print("Migrating customers table id column from INTEGER to TEXT...")
        c.execute('''
            CREATE TABLE customers_temp (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL DEFAULT 'default',
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                company TEXT,
                source TEXT DEFAULT 'direct',
                status TEXT NOT NULL DEFAULT 'active',
                risk_score REAL NOT NULL DEFAULT 0.5,
                total_conversations INTEGER NOT NULL DEFAULT 0,
                avg_sentiment REAL NOT NULL DEFAULT 0.5,
                total_tickets INTEGER NOT NULL DEFAULT 0,
                revenue_generated REAL NOT NULL DEFAULT 0.0,
                tags TEXT,
                notes TEXT,
                last_contact TEXT,
                created_at TEXT,
                updated_at TEXT,
                session_id TEXT
            )
        ''')
        c.execute('''
            INSERT INTO customers_temp (id, tenant_id, name, email, phone, company, source, status, risk_score, total_conversations, avg_sentiment, total_tickets, revenue_generated, tags, notes, last_contact, created_at, updated_at, session_id)
            SELECT CAST(id AS TEXT), COALESCE(tenant_id, 'default'), name, email, phone, company, source, status, risk_score, total_conversations, avg_sentiment, total_tickets, revenue_generated, tags, notes, last_contact, created_at, updated_at, session_id
            FROM customers
        ''')
        c.execute("DROP TABLE customers")
        c.execute("ALTER TABLE customers_temp RENAME TO customers")
        print("Customers table id column migrated to TEXT.")

    # Check if tickets.id is INTEGER
    c.execute("PRAGMA table_info(tickets)")
    t_cols = {row[1]: row[2] for row in c.fetchall()}
    if t_cols.get("id", "").upper().startswith("INT"):
        print("Migrating tickets table id column from INTEGER to TEXT...")
        c.execute('''
            CREATE TABLE tickets_temp (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL DEFAULT 'default',
                ticket_number INTEGER,
                customer_id TEXT,
                customer_name TEXT NOT NULL,
                issue TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN',
                priority TEXT NOT NULL DEFAULT 'MEDIUM',
                sentiment_score REAL NOT NULL DEFAULT 0.5,
                emotion TEXT NOT NULL DEFAULT 'neutral',
                intent TEXT,
                urgency_level TEXT NOT NULL DEFAULT 'LOW',
                channel TEXT NOT NULL DEFAULT 'dashboard',
                source TEXT NOT NULL DEFAULT 'dashboard',
                language TEXT NOT NULL DEFAULT 'en',
                assigned_agent_id TEXT,
                reply TEXT,
                resolved_at TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        c.execute('''
            INSERT INTO tickets_temp (id, tenant_id, ticket_number, customer_id, customer_name, issue, status, priority, sentiment_score, emotion, intent, urgency_level, channel, source, language, assigned_agent_id, reply, resolved_at, created_at, updated_at)
            SELECT CAST(id AS TEXT), COALESCE(tenant_id, 'default'), COALESCE(ticket_number, id), customer_id, customer_name, issue, status, priority, sentiment_score, emotion, intent, urgency_level, channel, source, language, assigned_agent_id, reply, resolved_at, created_at, updated_at
            FROM tickets
        ''')
        c.execute("DROP TABLE tickets")
        c.execute("ALTER TABLE tickets_temp RENAME TO tickets")
        print("Tickets table id column migrated to TEXT.")

    conn.commit()
    conn.close()
    print("Legacy table migration completed successfully.")

if __name__ == "__main__":
    migrate_legacy_tables()
