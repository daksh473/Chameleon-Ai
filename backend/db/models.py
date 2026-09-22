import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Numeric,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from db.base import Base, TimestampMixin, generate_uuid


# ==============================================================================
# CORE & MULTI-TENANCY
# ==============================================================================

class Tenant(Base, TimestampMixin):
    """
    Anchor entity for multi-tenancy. Every tenant is an isolated organization.
    """
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="tenant", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="tenant", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="tenant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="tenant", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="tenant", cascade="all, delete-orphan")
    analytics_snapshots = relationship("AnalyticsSnapshot", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_base_entries = relationship("KnowledgeBaseEntry", back_populates="tenant", cascade="all, delete-orphan")


class User(Base, TimestampMixin):
    """
    User/Agent belonging to a specific tenant.
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="member", nullable=False)  # admin, agent, member
    is_active = Column(Boolean, default=True, nullable=False)

    tenant = relationship("Tenant", back_populates="users")
    assigned_leads = relationship("Lead", back_populates="assigned_to", foreign_keys="Lead.assigned_to_user_id")
    assigned_tasks = relationship("Task", back_populates="assigned_to", foreign_keys="Task.assigned_to_user_id")
    assigned_tickets = relationship("Ticket", back_populates="assigned_agent", foreign_keys="Ticket.assigned_agent_id")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )


# ==============================================================================
# MODULE 1: CRM (Leads, Customers, Lead Activities)
# ==============================================================================

class Customer(Base, TimestampMixin):
    """
    CRM Customer record with historical activity and profile information.
    """
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    source = Column(String(100), default="direct", nullable=True)  # web, chat, email, telegram, manual
    status = Column(String(50), default="active", nullable=False)  # lead, active, inactive, churned
    risk_score = Column(Float, default=0.5, nullable=False)
    total_conversations = Column(Integer, default=0, nullable=False)
    avg_sentiment = Column(Float, default=0.5, nullable=False)
    total_tickets = Column(Integer, default=0, nullable=False)
    revenue_generated = Column(Numeric(12, 2), default=0.00, nullable=False)
    tags = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    last_contact = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="customers")
    leads = relationship("Lead", back_populates="customer")
    tickets = relationship("Ticket", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    orders = relationship("Order", back_populates="customer")
    tasks = relationship("Task", back_populates="customer")
    activities = relationship("LeadActivity", back_populates="customer", cascade="all, delete-orphan")


class Lead(Base, TimestampMixin):
    """
    CRM Lead opportunity pipeline.
    Statuses: new, contacted, qualified, proposal, won, lost
    """
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)  # Deal / Opportunity Title
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    status = Column(String(50), default="new", nullable=False, index=True)  # new, contacted, qualified, proposal, won, lost
    estimated_value = Column(Numeric(12, 2), default=0.00, nullable=False)
    probability = Column(Integer, default=20, nullable=False)  # 0 to 100 percentage
    source = Column(String(100), default="web", nullable=True)
    assigned_to_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    tenant = relationship("Tenant", back_populates="leads")
    customer = relationship("Customer", back_populates="leads")
    assigned_to = relationship("User", back_populates="assigned_leads", foreign_keys=[assigned_to_user_id])
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="lead")


class LeadActivity(Base):
    """
    Timeline audit trail of interactions with a lead or customer.
    """
    __tablename__ = "lead_activities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True)
    activity_type = Column(String(50), nullable=False)  # call, email, meeting, note, status_change
    description = Column(Text, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    performed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    lead = relationship("Lead", back_populates="activities")
    customer = relationship("Customer", back_populates="activities")


# ==============================================================================
# MODULE 2: SUPPORT (Tickets, Conversations, Knowledge Base)
# ==============================================================================

class Ticket(Base, TimestampMixin):
    """
    Support ticket migrated from existing schema, maintaining full compatibility
    with AI sentiment analysis, channel ingestion, and escalation.
    """
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_number = Column(Integer, nullable=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_name = Column(String(255), nullable=False)
    issue = Column(Text, nullable=False)
    status = Column(String(50), default="OPEN", nullable=False, index=True)  # OPEN, IN_PROGRESS, ESCALATED, RESOLVED, CLOSED
    priority = Column(String(50), default="MEDIUM", nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    sentiment_score = Column(Float, default=0.5, nullable=False)
    emotion = Column(String(50), default="neutral", nullable=False)
    intent = Column(String(100), nullable=True)
    urgency_level = Column(String(50), default="LOW", nullable=False)
    channel = Column(String(50), default="dashboard", nullable=False)  # dashboard, telegram, email, whatsapp, voice
    source = Column(String(100), default="dashboard", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    assigned_agent_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reply = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="tickets")
    customer = relationship("Customer", back_populates="tickets")
    assigned_agent = relationship("User", back_populates="assigned_tickets", foreign_keys=[assigned_agent_id])
    conversation_messages = relationship("ConversationMessage", back_populates="ticket", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="ticket")


class ConversationMessage(Base):
    """
    Individual chat / email / telegram message tied to a session or ticket.
    """
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, agent, system
    message = Column(Text, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    emotion = Column(String(50), nullable=True)
    action = Column(String(50), nullable=True)
    language = Column(String(10), default="en", nullable=False)
    channel = Column(String(50), default="dashboard", nullable=False)
    source = Column(String(50), default="ai_generated", nullable=False)
    sender_id = Column(String(255), nullable=True)
    sender_name = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    ticket = relationship("Ticket", back_populates="conversation_messages")


class KnowledgeBaseEntry(Base, TimestampMixin):
    """
    Tenant-specific knowledge base FAQs for AI auto-reply.
    """
    __tablename__ = "knowledge_base_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), default="general", nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    language = Column(String(10), default="en", nullable=False)

    tenant = relationship("Tenant", back_populates="knowledge_base_entries")


# ==============================================================================
# MODULE 3: BILLING (Invoices, Invoice Items)
# ==============================================================================

class Invoice(Base, TimestampMixin):
    """
    Customer invoice with line items, due dates, and reminders.
    """
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=True, index=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="draft", nullable=False, index=True)  # draft, pending, paid, overdue, cancelled
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    subtotal = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    notes = Column(Text, nullable=True)
    pdf_url = Column(String(500), nullable=True)
    last_reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "invoice_number", name="uq_invoices_tenant_number"),
    )


class InvoiceItem(Base):
    """
    Line item inside an invoice.
    """
    __tablename__ = "invoice_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")


# ==============================================================================
# MODULE 4: INVENTORY (Products, Orders, Order Items)
# ==============================================================================

class Product(Base, TimestampMixin):
    """
    Catalog product with inventory stock tracking and low-stock alerting.
    """
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    unit_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    cost_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    min_stock_threshold = Column(Integer, default=10, nullable=False)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    tenant = relationship("Tenant", back_populates="products")

    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),
    )


class Order(Base, TimestampMixin):
    """
    Sales/fulfillment order with stock decrement on fulfillment.
    """
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    order_number = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, processing, fulfilled, cancelled
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    notes = Column(Text, nullable=True)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="order")

    __table_args__ = (
        UniqueConstraint("tenant_id", "order_number", name="uq_orders_tenant_number"),
    )


class OrderItem(Base):
    """
    Line item inside an order specifying product and quantity.
    """
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")


# ==============================================================================
# MODULE 5: TASKS (Internal Team Tasks)
# ==============================================================================

class Task(Base, TimestampMixin):
    """
    Internal task management optionally linked to Leads, Tickets, Orders, or Customers.
    """
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="todo", nullable=False, index=True)  # todo, in_progress, done
    priority = Column(String(50), default="medium", nullable=False)  # low, medium, high, urgent
    due_date = Column(DateTime(timezone=True), nullable=True)
    assigned_to_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Polymorphic linkages
    lead_id = Column(String(36), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)

    tenant = relationship("Tenant", back_populates="tasks")
    assigned_to = relationship("User", back_populates="assigned_tasks", foreign_keys=[assigned_to_user_id])
    lead = relationship("Lead", back_populates="tasks")
    customer = relationship("Customer", back_populates="tasks")
    ticket = relationship("Ticket", back_populates="tasks")
    order = relationship("Order", back_populates="tasks")


# ==============================================================================
# MODULE 6: ANALYTICS (Daily Periodic Snapshots)
# ==============================================================================

class AnalyticsSnapshot(Base):
    """
    Daily snapshot for fast, cached executive dashboard reporting.
    """
    __tablename__ = "analytics_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    open_tickets = Column(Integer, default=0, nullable=False)
    revenue_this_month = Column(Numeric(14, 2), default=0.00, nullable=False)
    new_leads_this_week = Column(Integer, default=0, nullable=False)
    pending_orders = Column(Integer, default=0, nullable=False)
    overdue_invoices = Column(Integer, default=0, nullable=False)
    task_completion_rate = Column(Float, default=0.0, nullable=False)  # 0.0 - 100.0 %
    metrics_json = Column(Text, nullable=True)  # Extended breakdown JSON
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    tenant = relationship("Tenant", back_populates="analytics_snapshots")

    __table_args__ = (
        UniqueConstraint("tenant_id", "snapshot_date", name="uq_analytics_tenant_date"),
    )
