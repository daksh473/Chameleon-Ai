"""0001_initial_multi_tenant_schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-09-22 04:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tenants (Anchor table)
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)

    # 2. Users (Tenancy auth entity)
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='member'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_users_tenant_email')
    )
    op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)

    # 3. CRM Customers
    op.create_table(
        'customers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True, server_default='direct'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('total_conversations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_sentiment', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('total_tickets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('revenue_generated', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_contact', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_tenant_id'), 'customers', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=False)

    # 4. Inventory Products (Created before invoice_items / order_items)
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('cost_price', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_stock_threshold', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'sku', name='uq_products_tenant_sku')
    )
    op.create_index(op.f('ix_products_tenant_id'), 'products', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_products_sku'), 'products', ['sku'], unique=False)

    # 5. CRM Leads (pipeline)
    op.create_table(
        'leads',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='new'),
        sa.Column('estimated_value', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('probability', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('source', sa.String(length=100), nullable=True, server_default='web'),
        sa.Column('assigned_to_user_id', sa.String(length=36), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_tenant_id'), 'leads', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_leads_customer_id'), 'leads', ['customer_id'], unique=False)
    op.create_index(op.f('ix_leads_status'), 'leads', ['status'], unique=False)
    op.create_index(op.f('ix_leads_email'), 'leads', ['email'], unique=False)
    op.create_index(op.f('ix_leads_assigned_to_user_id'), 'leads', ['assigned_to_user_id'], unique=False)

    # 6. CRM Lead Activities
    op.create_table(
        'lead_activities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('lead_id', sa.String(length=36), nullable=True),
        sa.Column('customer_id', sa.String(length=36), nullable=True),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('performed_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_activities_tenant_id'), 'lead_activities', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_lead_activities_customer_id'), 'lead_activities', ['customer_id'], unique=False)
    op.create_index(op.f('ix_lead_activities_lead_id'), 'lead_activities', ['lead_id'], unique=False)

    # 7. Support Tickets
    op.create_table(
        'tickets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('ticket_number', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.String(length=36), nullable=True),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('issue', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('sentiment_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('emotion', sa.String(length=50), nullable=False, server_default='neutral'),
        sa.Column('intent', sa.String(length=100), nullable=True),
        sa.Column('urgency_level', sa.String(length=50), nullable=False, server_default='LOW'),
        sa.Column('channel', sa.String(length=50), nullable=False, server_default='dashboard'),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='dashboard'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('assigned_agent_id', sa.String(length=36), nullable=True),
        sa.Column('reply', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assigned_agent_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tickets_tenant_id'), 'tickets', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_tickets_customer_id'), 'tickets', ['customer_id'], unique=False)
    op.create_index(op.f('ix_tickets_status'), 'tickets', ['status'], unique=False)
    op.create_index(op.f('ix_tickets_priority'), 'tickets', ['priority'], unique=False)
    op.create_index(op.f('ix_tickets_assigned_agent_id'), 'tickets', ['assigned_agent_id'], unique=False)

    # 8. Support Conversation Messages
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('ticket_id', sa.String(length=36), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('emotion', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('channel', sa.String(length=50), nullable=False, server_default='dashboard'),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='ai_generated'),
        sa.Column('sender_id', sa.String(length=255), nullable=True),
        sa.Column('sender_name', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_messages_tenant_id'), 'conversation_messages', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_conversation_messages_session_id'), 'conversation_messages', ['session_id'], unique=False)
    op.create_index(op.f('ix_conversation_messages_ticket_id'), 'conversation_messages', ['ticket_id'], unique=False)

    # 9. Support Knowledge Base
    op.create_table(
        'knowledge_base_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='general'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_base_entries_tenant_id'), 'knowledge_base_entries', ['tenant_id'], unique=False)

    # 10. Billing Invoices
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=True),
        sa.Column('invoice_number', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('pdf_url', sa.String(length=500), nullable=True),
        sa.Column('last_reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'invoice_number', name='uq_invoices_tenant_number')
    )
    op.create_index(op.f('ix_invoices_tenant_id'), 'invoices', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_invoices_customer_id'), 'invoices', ['customer_id'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_number'), 'invoices', ['invoice_number'], unique=False)
    op.create_index(op.f('ix_invoices_status'), 'invoices', ['status'], unique=False)

    # 11. Billing Invoice Items (references products)
    op.create_table(
        'invoice_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_items_tenant_id'), 'invoice_items', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_invoice_items_invoice_id'), 'invoice_items', ['invoice_id'], unique=False)

    # 12. Inventory Orders
    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=True),
        sa.Column('order_number', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('fulfilled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'order_number', name='uq_orders_tenant_number')
    )
    op.create_index(op.f('ix_orders_tenant_id'), 'orders', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)

    # 13. Inventory Order Items (references orders & products)
    op.create_table(
        'order_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_items_tenant_id'), 'order_items', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_items_product_id'), 'order_items', ['product_id'], unique=False)

    # 14. Tasks (linked to leads, tickets, orders, customers, users)
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='todo'),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='medium'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to_user_id', sa.String(length=36), nullable=True),
        sa.Column('lead_id', sa.String(length=36), nullable=True),
        sa.Column('customer_id', sa.String(length=36), nullable=True),
        sa.Column('ticket_id', sa.String(length=36), nullable=True),
        sa.Column('order_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_tenant_id'), 'tasks', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_tasks_assigned_to_user_id'), 'tasks', ['assigned_to_user_id'], unique=False)
    op.create_index(op.f('ix_tasks_customer_id'), 'tasks', ['customer_id'], unique=False)
    op.create_index(op.f('ix_tasks_lead_id'), 'tasks', ['lead_id'], unique=False)
    op.create_index(op.f('ix_tasks_order_id'), 'tasks', ['order_id'], unique=False)
    op.create_index(op.f('ix_tasks_ticket_id'), 'tasks', ['ticket_id'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)

    # 15. Analytics Snapshots
    op.create_table(
        'analytics_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('open_tickets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('revenue_this_month', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('new_leads_this_week', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pending_orders', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overdue_invoices', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('task_completion_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('metrics_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'snapshot_date', name='uq_analytics_tenant_date')
    )
    op.create_index(op.f('ix_analytics_snapshots_tenant_id'), 'analytics_snapshots', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_analytics_snapshots_snapshot_date'), 'analytics_snapshots', ['snapshot_date'], unique=False)


def downgrade() -> None:
    op.drop_table('analytics_snapshots')
    op.drop_table('tasks')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('invoice_items')
    op.drop_table('products')
    op.drop_table('invoices')
    op.drop_table('knowledge_base_entries')
    op.drop_table('conversation_messages')
    op.drop_table('tickets')
    op.drop_table('lead_activities')
    op.drop_table('leads')
    op.drop_table('customers')
    op.drop_table('users')
    op.drop_table('tenants')
