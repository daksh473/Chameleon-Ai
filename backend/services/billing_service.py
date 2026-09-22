import os
import io
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from db.models import Invoice, InvoiceItem, Customer, Tenant
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)


# Path for saving static PDF files
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
INVOICES_DIR = os.path.join(STATIC_DIR, "invoices")
os.makedirs(INVOICES_DIR, exist_ok=True)


# ==============================================================================
# INVOICE NUMBER GENERATOR
# ==============================================================================

def generate_invoice_number(db: Session, tenant_id: str) -> str:
    """
    Generate sequential invoice number: INV-YYYY-XXXX (e.g. INV-2026-0001).
    Scoped strictly by tenant_id.
    """
    current_year = datetime.now().year
    prefix = f"INV-{current_year}-"

    # Count existing invoices for this year and tenant
    existing_count = db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.invoice_number.like(f"{prefix}%")
    ).count()

    seq = existing_count + 1
    # Check for uniqueness, increment if collided
    while True:
        candidate = f"{prefix}{seq:04d}"
        exists = db.query(Invoice.id).filter(
            Invoice.tenant_id == tenant_id,
            Invoice.invoice_number == candidate
        ).first()
        if not exists:
            return candidate
        seq += 1


# ==============================================================================
# INVOICE CRUD OPERATIONS
# ==============================================================================

def create_invoice(
    db: Session,
    tenant_id: str,
    items: List[Dict[str, Any]],
    customer_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
    issue_date: Optional[date] = None,
    due_date: Optional[date] = None,
    tax_rate: float = 0.0,
    tax_amount: Optional[float] = None,
    discount_amount: float = 0.0,
    notes: Optional[str] = None,
    status: str = "pending",
    auto_generate_pdf: bool = True,
) -> Invoice:
    """
    Create a new invoice with line items strictly tied to tenant_id.
    Calculates subtotal, tax, and total.
    """
    if not items:
        raise ValueError("At least one line item is required to create an invoice.")

    # Auto-resolve or create customer if name/email provided without customer_id
    if not customer_id and customer_name:
        cust = db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            or_(Customer.name == customer_name, Customer.email == customer_email)
        ).first()
        if not cust:
            cust = Customer(
                tenant_id=tenant_id,
                name=customer_name,
                email=customer_email,
                status="active"
            )
            db.add(cust)
            db.commit()
            db.refresh(cust)
        customer_id = cust.id
    elif customer_id:
        # Validate customer belongs to this tenant
        cust = db.query(Customer).filter(
            Customer.tenant_id == tenant_id,
            Customer.id == customer_id
        ).first()
        if not cust:
            raise ValueError(f"Customer {customer_id} does not exist in this tenant.")

    today = date.today()
    inv_issue_date = issue_date or today
    inv_due_date = due_date or (inv_issue_date + timedelta(days=30))

    # Calculate item totals and invoice subtotal
    calculated_items = []
    subtotal = 0.0
    for itm in items:
        desc = itm.get("description", "Item")
        qty = int(itm.get("quantity", 1))
        if qty <= 0:
            qty = 1
        unit_price = float(itm.get("unit_price", 0.0))
        item_total = round(qty * unit_price, 2)
        subtotal += item_total
        calculated_items.append({
            "product_id": itm.get("product_id"),
            "description": desc,
            "quantity": qty,
            "unit_price": unit_price,
            "total_amount": item_total,
        })

    subtotal = round(subtotal, 2)
    if tax_amount is None:
        computed_tax = round(subtotal * (float(tax_rate) / 100.0), 2)
    else:
        computed_tax = round(float(tax_amount), 2)

    discount = round(float(discount_amount), 2)
    total_amount = max(0.0, round(subtotal + computed_tax - discount, 2))

    inv_num = generate_invoice_number(db, tenant_id)

    invoice = Invoice(
        tenant_id=tenant_id,
        customer_id=customer_id,
        invoice_number=inv_num,
        status=status.lower(),
        issue_date=inv_issue_date,
        due_date=inv_due_date,
        subtotal=subtotal,
        tax_amount=computed_tax,
        discount_amount=discount,
        total_amount=total_amount,
        notes=notes,
        pdf_url=None,
        paid_at=datetime.now(timezone.utc) if status.lower() == "paid" else None,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Insert items
    for ci in calculated_items:
        item_row = InvoiceItem(
            tenant_id=tenant_id,
            invoice_id=invoice.id,
            product_id=ci["product_id"],
            description=ci["description"],
            quantity=ci["quantity"],
            unit_price=ci["unit_price"],
            total_amount=ci["total_amount"],
        )
        db.add(item_row)

    # If marked paid at creation and customer attached, update customer revenue
    if invoice.status == "paid" and customer_id:
        cust = db.query(Customer).filter(Customer.tenant_id == tenant_id, Customer.id == customer_id).first()
        if cust:
            cust.revenue_generated = float(cust.revenue_generated or 0.0) + total_amount

    db.commit()
    db.refresh(invoice)

    # Generate PDF if requested
    if auto_generate_pdf:
        try:
            pdf_path, pdf_url = generate_and_save_invoice_pdf(db, invoice)
            invoice.pdf_url = pdf_url
            db.commit()
            db.refresh(invoice)
        except Exception as e:
            print(f"Warning: PDF generation failed during invoice creation: {e}")

    return invoice


def get_invoices(
    db: Session,
    tenant_id: str,
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List invoices strictly filtered by tenant_id with customer details.
    Zero cross-tenant leakage.
    """
    query = db.query(Invoice).filter(Invoice.tenant_id == tenant_id)

    if status and status.lower() != "all":
        query = query.filter(Invoice.status == status.lower())

    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    if search:
        search_term = f"%{search.strip()}%"
        # Join with Customer to search by customer name or invoice number
        query = query.outerjoin(Customer, Invoice.customer_id == Customer.id).filter(
            or_(
                Invoice.invoice_number.ilike(search_term),
                Customer.name.ilike(search_term),
                Customer.email.ilike(search_term),
            )
        )

    total_count = query.count()
    invoices = query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for inv in invoices:
        cust = inv.customer
        item_count = len(inv.items)
        results.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "customer_id": inv.customer_id,
            "customer_name": cust.name if cust else "Direct / Unassigned",
            "customer_email": cust.email if cust else None,
            "status": inv.status,
            "issue_date": str(inv.issue_date),
            "due_date": str(inv.due_date),
            "subtotal": float(inv.subtotal),
            "tax_amount": float(inv.tax_amount),
            "discount_amount": float(inv.discount_amount),
            "total_amount": float(inv.total_amount),
            "notes": inv.notes,
            "pdf_url": inv.pdf_url,
            "items_count": item_count,
            "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        })

    return results, total_count


def get_invoice_by_id(db: Session, tenant_id: str, invoice_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single invoice with full line items strictly isolated to tenant_id.
    """
    inv = db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.id == invoice_id
    ).first()

    if not inv:
        return None

    cust = inv.customer
    items = [
        {
            "id": itm.id,
            "product_id": itm.product_id,
            "description": itm.description,
            "quantity": itm.quantity,
            "unit_price": float(itm.unit_price),
            "total_amount": float(itm.total_amount),
        }
        for itm in inv.items
    ]

    return {
        "id": inv.id,
        "tenant_id": inv.tenant_id,
        "invoice_number": inv.invoice_number,
        "customer_id": inv.customer_id,
        "customer": {
            "id": cust.id,
            "name": cust.name,
            "email": cust.email,
            "phone": cust.phone,
            "company": cust.company,
        } if cust else None,
        "status": inv.status,
        "issue_date": str(inv.issue_date),
        "due_date": str(inv.due_date),
        "subtotal": float(inv.subtotal),
        "tax_amount": float(inv.tax_amount),
        "discount_amount": float(inv.discount_amount),
        "total_amount": float(inv.total_amount),
        "notes": inv.notes,
        "pdf_url": inv.pdf_url,
        "items": items,
        "last_reminder_sent_at": inv.last_reminder_sent_at.isoformat() if inv.last_reminder_sent_at else None,
        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


def update_invoice_status(
    db: Session,
    tenant_id: str,
    invoice_id: str,
    status: str
) -> Optional[Invoice]:
    """
    Update invoice status (draft, pending, paid, overdue, cancelled).
    Syncs customer revenue_generated when transitioned to or from 'paid'.
    Regenerates PDF to reflect the updated status stamp.
    """
    valid_statuses = {"draft", "pending", "paid", "overdue", "cancelled"}
    new_status = status.lower()
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")

    inv = db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.id == invoice_id
    ).first()

    if not inv:
        return None

    old_status = inv.status
    inv.status = new_status

    # Customer revenue synchronization
    if inv.customer_id:
        cust = db.query(Customer).filter(Customer.tenant_id == tenant_id, Customer.id == inv.customer_id).first()
        if cust:
            current_rev = float(cust.revenue_generated or 0.0)
            inv_total = float(inv.total_amount)

            if old_status != "paid" and new_status == "paid":
                cust.revenue_generated = current_rev + inv_total
                inv.paid_at = datetime.now(timezone.utc)
            elif old_status == "paid" and new_status != "paid":
                cust.revenue_generated = max(0.0, current_rev - inv_total)
                inv.paid_at = None

    if new_status == "paid" and not inv.paid_at:
        inv.paid_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(inv)

    # Regenerate PDF to update status badge
    try:
        pdf_path, pdf_url = generate_and_save_invoice_pdf(db, inv)
        inv.pdf_url = pdf_url
        db.commit()
        db.refresh(inv)
    except Exception as e:
        print(f"Warning: PDF refresh failed on status change: {e}")

    return inv


def delete_invoice(db: Session, tenant_id: str, invoice_id: str) -> bool:
    """
    Delete an invoice and its line items strictly isolated to tenant_id.
    """
    inv = db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.id == invoice_id
    ).first()

    if not inv:
        return False

    # If was paid, decrement customer revenue
    if inv.status == "paid" and inv.customer_id:
        cust = db.query(Customer).filter(Customer.tenant_id == tenant_id, Customer.id == inv.customer_id).first()
        if cust:
            cust.revenue_generated = max(0.0, float(cust.revenue_generated or 0.0) - float(inv.total_amount))

    # Remove physical PDF file if exists
    if inv.pdf_url:
        filename = f"{inv.invoice_number}.pdf"
        target_path = os.path.join(INVOICES_DIR, tenant_id, filename)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except OSError:
                pass

    db.delete(inv)
    db.commit()
    return True


def get_billing_stats(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Compute billing KPI metrics strictly isolated by tenant_id.
    """
    total_invoices = db.query(Invoice).filter(Invoice.tenant_id == tenant_id).count()
    paid_count = db.query(Invoice).filter(Invoice.tenant_id == tenant_id, Invoice.status == "paid").count()
    overdue_count = db.query(Invoice).filter(Invoice.tenant_id == tenant_id, Invoice.status == "overdue").count()
    pending_count = db.query(Invoice).filter(Invoice.tenant_id == tenant_id, Invoice.status.in_(["pending", "draft"])).count()
    cancelled_count = db.query(Invoice).filter(Invoice.tenant_id == tenant_id, Invoice.status == "cancelled").count()

    total_revenue = db.query(func.sum(Invoice.total_amount)).filter(
        Invoice.tenant_id == tenant_id, Invoice.status == "paid"
    ).scalar() or 0.0

    pending_amount = db.query(func.sum(Invoice.total_amount)).filter(
        Invoice.tenant_id == tenant_id, Invoice.status.in_(["pending", "draft"])
    ).scalar() or 0.0

    overdue_amount = db.query(func.sum(Invoice.total_amount)).filter(
        Invoice.tenant_id == tenant_id, Invoice.status == "overdue"
    ).scalar() or 0.0

    return {
        "total_invoices": total_invoices,
        "paid_invoices": paid_count,
        "overdue_invoices": overdue_count,
        "pending_invoices": pending_count,
        "cancelled_invoices": cancelled_count,
        "total_revenue": float(total_revenue),
        "pending_amount": float(pending_amount),
        "overdue_amount": float(overdue_amount),
    }


# ==============================================================================
# PDF GENERATION (ReportLab)
# ==============================================================================

def generate_invoice_pdf_bytes(invoice: Invoice, tenant_name: str = "Chameleon AI") -> bytes:
    """
    Builds a professional invoice PDF in memory using ReportLab.
    Emphasizes vibrant emerald green accents and clean layout.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    
    # Custom Emerald Green palette
    COLOR_PRIMARY = colors.HexColor("#10B981")     # Emerald green
    COLOR_DARK = colors.HexColor("#064E3B")        # Deep forest green
    COLOR_BG_HEADER = colors.HexColor("#ECFDF5")   # Very light emerald
    COLOR_TEXT_MAIN = colors.HexColor("#0F172A")   # Slate 900
    COLOR_TEXT_MUTED = colors.HexColor("#64748B")  # Slate 500
    COLOR_BORDER = colors.HexColor("#CBD5E1")      # Slate 300

    # Status color mapping
    status_colors = {
        "paid": colors.HexColor("#10B981"),
        "pending": colors.HexColor("#F59E0B"),
        "overdue": colors.HexColor("#EF4444"),
        "draft": colors.HexColor("#6B7280"),
        "cancelled": colors.HexColor("#9CA3AF"),
    }
    status_color = status_colors.get(invoice.status.lower(), COLOR_PRIMARY)

    subtitle_style = ParagraphStyle(
        "InvoiceSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=COLOR_TEXT_MAIN,
        leading=16,
    )

    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=COLOR_TEXT_MUTED,
        leading=12,
    )

    status_badge_style = ParagraphStyle(
        "StatusBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=status_color,
        alignment=2,  # Right aligned
        leading=15,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=COLOR_TEXT_MAIN,
        leading=13,
    )

    body_bold_style = ParagraphStyle(
        "BodyBoldCustom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=COLOR_TEXT_MAIN,
        leading=13,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.white,
        leading=12,
    )

    elements = []

    # 1. Top Header Banner Table (Brand + INVOICE header)
    header_data = [
        [
            Paragraph(f"<b>{tenant_name}</b><br/><font size=8 color='#64748B'>Business Management System</font>", subtitle_style),
            Paragraph(f"INVOICE<br/><font size=11 color='{status_color.hexval()}'>● {invoice.status.upper()}</font>", status_badge_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[300, 240])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_PRIMARY, spaceBefore=4, spaceAfter=15))

    # 2. Metadata Block (Billed To vs Invoice Details)
    customer = invoice.customer
    cust_name = customer.name if customer else "Direct Customer"
    cust_email = customer.email if customer and customer.email else "N/A"
    cust_phone = customer.phone if customer and customer.phone else ""
    cust_company = customer.company if customer and customer.company else ""

    billed_to_text = f"<b>{cust_name}</b>"
    if cust_company:
        billed_to_text += f"<br/>{cust_company}"
    if cust_email != "N/A":
        billed_to_text += f"<br/>{cust_email}"
    if cust_phone:
        billed_to_text += f"<br/>{cust_phone}"

    meta_grid = [
        [
            Paragraph("<b>BILLED TO</b>", meta_label_style),
            Paragraph("<b>INVOICE DETAILS</b>", meta_label_style)
        ],
        [
            Paragraph(billed_to_text, body_style),
            Paragraph(
                f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
                f"<b>Issue Date:</b> {invoice.issue_date}<br/>"
                f"<b>Due Date:</b> {invoice.due_date}<br/>"
                f"<b>Status:</b> {invoice.status.capitalize()}",
                body_style
            )
        ]
    ]
    meta_table = Table(meta_grid, colWidths=[300, 240])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # 3. Line Items Table
    table_rows = [
        [
            Paragraph("<b>#</b>", table_header_style),
            Paragraph("<b>Description</b>", table_header_style),
            Paragraph("<b>Qty</b>", table_header_style),
            Paragraph("<b>Unit Price</b>", table_header_style),
            Paragraph("<b>Amount</b>", table_header_style)
        ]
    ]

    for idx, item in enumerate(invoice.items, start=1):
        table_rows.append([
            Paragraph(str(idx), body_style),
            Paragraph(item.description, body_style),
            Paragraph(str(item.quantity), body_style),
            Paragraph(f"${float(item.unit_price):,.2f}", body_style),
            Paragraph(f"<b>${float(item.total_amount):,.2f}</b>", body_style),
        ])

    items_table = Table(table_rows, colWidths=[30, 270, 50, 95, 95])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_BG_HEADER]),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))

    # 4. Calculation Summary Table (Right Aligned)
    summary_data = [
        [Paragraph("Subtotal:", body_bold_style), Paragraph(f"${float(invoice.subtotal):,.2f}", body_style)],
        [Paragraph("Tax:", body_bold_style), Paragraph(f"${float(invoice.tax_amount):,.2f}", body_style)],
    ]
    if float(invoice.discount_amount) > 0:
        summary_data.append([
            Paragraph("Discount:", body_bold_style),
            Paragraph(f"-${float(invoice.discount_amount):,.2f}", body_style)
        ])
    summary_data.append([
        Paragraph("<b>Total Amount:</b>", ParagraphStyle("SummaryTotal", parent=body_bold_style, fontSize=11, textColor=COLOR_PRIMARY)),
        Paragraph(f"<b>${float(invoice.total_amount):,.2f}</b>", ParagraphStyle("SummaryTotalVal", parent=body_bold_style, fontSize=11, textColor=COLOR_PRIMARY))
    ])

    summary_table = Table(summary_data, colWidths=[120, 100])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, COLOR_PRIMARY),
    ]))

    # Place summary in a 2-column container to push it right
    notes_content = f"<b>Notes:</b><br/>{invoice.notes}" if invoice.notes else "<b>Payment Terms:</b><br/>Payment due by the specified date. Thank you for your business!"
    notes_paragraph = Paragraph(notes_content, ParagraphStyle("NotesStyle", parent=body_style, textColor=COLOR_TEXT_MUTED))

    total_container_data = [
        [notes_paragraph, summary_table]
    ]
    total_container = Table(total_container_data, colWidths=[320, 220])
    total_container.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(KeepTogether(total_container))
    elements.append(Spacer(1, 30))

    # 5. Footer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceBefore=10, spaceAfter=8))
    footer_text = f"Generated by {tenant_name} BMS • Multi-Tenant Enterprise Architecture"
    elements.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=meta_label_style, alignment=1)))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_and_save_invoice_pdf(db: Session, invoice: Invoice) -> Tuple[str, str]:
    """
    Generates and saves the invoice PDF to disk.
    Returns (absolute_file_path, web_url_path).
    """
    tenant = db.query(Tenant).filter(Tenant.id == invoice.tenant_id).first()
    tenant_name = tenant.name if tenant else "Chameleon AI"

    tenant_folder = os.path.join(INVOICES_DIR, invoice.tenant_id)
    os.makedirs(tenant_folder, exist_ok=True)

    filename = f"{invoice.invoice_number}.pdf"
    file_path = os.path.join(tenant_folder, filename)

    pdf_bytes = generate_invoice_pdf_bytes(invoice, tenant_name=tenant_name)
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    # Relative URL accessible via static or API endpoint
    web_url = f"/billing/invoices/{invoice.id}/pdf"
    return file_path, web_url


def get_invoice_pdf_path(db: Session, tenant_id: str, invoice_id: str) -> Optional[str]:
    """
    Get or regenerate the absolute file path for an invoice PDF.
    Guarantees that a valid PDF file exists on disk.
    """
    inv = db.query(Invoice).filter(
        Invoice.tenant_id == tenant_id,
        Invoice.id == invoice_id
    ).first()

    if not inv:
        return None

    tenant_folder = os.path.join(INVOICES_DIR, tenant_id)
    os.makedirs(tenant_folder, exist_ok=True)
    file_path = os.path.join(tenant_folder, f"{inv.invoice_number}.pdf")

    if not os.path.exists(file_path):
        # Regenerate on the fly
        generate_and_save_invoice_pdf(db, inv)

    return file_path


# ==============================================================================
# APSCHEDULER OVERDUE & REMINDER CHECK
# ==============================================================================

def check_and_update_overdue_invoices(db: Session, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Background worker job:
    1. Finds all 'pending' invoices whose due_date < today and marks them 'overdue'.
    2. Updates last_reminder_sent_at timestamp.
    3. Scoped by tenant_id if provided, or across all tenants if tenant_id is None.
    """
    today = date.today()
    query = db.query(Invoice).filter(
        Invoice.status == "pending",
        Invoice.due_date < today
    )

    if tenant_id:
        query = query.filter(Invoice.tenant_id == tenant_id)

    overdue_invoices = query.all()
    updated_records = []

    now = datetime.now(timezone.utc)
    for inv in overdue_invoices:
        inv.status = "overdue"
        inv.last_reminder_sent_at = now
        updated_records.append({
            "id": inv.id,
            "tenant_id": inv.tenant_id,
            "invoice_number": inv.invoice_number,
            "due_date": str(inv.due_date),
            "total_amount": float(inv.total_amount),
            "status": inv.status
        })

    if updated_records:
        db.commit()

    return updated_records
