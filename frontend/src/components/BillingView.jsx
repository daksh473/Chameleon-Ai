import { useState, useEffect } from "react";
import {
  FileText,
  DollarSign,
  CheckCircle,
  AlertTriangle,
  Clock,
  Plus,
  Trash2,
  Download,
  Eye,
  RefreshCw,
  Search,
  X,
  Send,
  Zap,
  Check,
} from "lucide-react";
import "./BillingView.css";

const API = "http://localhost:8000";

export default function BillingView() {
  const [stats, setStats] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Create Form State
  const [formCustomerId, setFormCustomerId] = useState("");
  const [formCustomName, setFormCustomName] = useState("");
  const [formCustomEmail, setFormCustomEmail] = useState("");
  const [formIssueDate, setFormIssueDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [formDueDate, setFormDueDate] = useState(
    new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0]
  );
  const [formTaxRate, setFormTaxRate] = useState(10);
  const [formDiscount, setFormDiscount] = useState(0);
  const [formNotes, setFormNotes] = useState("");
  const [formStatus, setFormStatus] = useState("pending");
  const [formItems, setFormItems] = useState([
    { description: "", quantity: 1, unit_price: 0 },
  ]);
  const [submitting, setSubmitting] = useState(false);

  // Show temporary toast notification
  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Fetch stats & invoices
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, invRes, custRes] = await Promise.all([
        fetch(`${API}/billing/stats`).then((r) => (r.ok ? r.json() : null)),
        fetch(
          `${API}/billing/invoices?status=${activeFilter}&search=${encodeURIComponent(
            searchQuery
          )}`
        ).then((r) => (r.ok ? r.json() : { invoices: [] })),
        fetch(`${API}/crm/customers`).then((r) => (r.ok ? r.json() : [])),
      ]);

      setStats(statsRes);
      setInvoices(invRes.invoices || []);
      setCustomers(Array.isArray(custRes) ? custRes : []);
    } catch (err) {
      console.error("Billing fetch error:", err);
      setError("Failed to connect to billing service.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchData();
  };

  // Trigger Overdue Scanner Job
  const handleTriggerScanner = async () => {
    try {
      const res = await fetch(`${API}/billing/reminders/trigger`, {
        method: "POST",
      });
      const data = await res.json();
      showToast(data.message || "Overdue check completed.");
      fetchData();
    } catch (err) {
      showToast("Error triggering reminder scan.");
    }
  };

  // Mark invoice as paid
  const handleMarkAsPaid = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/billing/invoices/${invoiceId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "paid" }),
      });
      if (res.ok) {
        showToast("Invoice marked as PAID! Revenue updated.");
        fetchData();
        if (selectedInvoice && selectedInvoice.id === invoiceId) {
          const updated = await fetch(`${API}/billing/invoices/${invoiceId}`).then(
            (r) => r.json()
          );
          setSelectedInvoice(updated);
        }
      }
    } catch (err) {
      showToast("Failed to update invoice status.");
    }
  };

  // Delete invoice
  const handleDeleteInvoice = async (invoiceId) => {
    if (!window.confirm("Are you sure you want to delete this invoice?")) return;
    try {
      const res = await fetch(`${API}/billing/invoices/${invoiceId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        showToast("Invoice deleted successfully.");
        if (selectedInvoice?.id === invoiceId) setSelectedInvoice(null);
        fetchData();
      }
    } catch (err) {
      showToast("Failed to delete invoice.");
    }
  };

  // View invoice detail
  const handleViewInvoice = async (invoiceId) => {
    try {
      const res = await fetch(`${API}/billing/invoices/${invoiceId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedInvoice(data);
      }
    } catch (err) {
      showToast("Failed to load invoice details.");
    }
  };

  // Download PDF
  const handleDownloadPdf = (invoiceId) => {
    window.open(`${API}/billing/invoices/${invoiceId}/pdf`, "_blank");
  };

  // Form item row operations
  const handleAddItemRow = () => {
    setFormItems([...formItems, { description: "", quantity: 1, unit_price: 0 }]);
  };

  const handleRemoveItemRow = (idx) => {
    if (formItems.length === 1) return;
    setFormItems(formItems.filter((_, i) => i !== idx));
  };

  const handleItemChange = (idx, field, val) => {
    const next = [...formItems];
    next[idx][field] = val;
    setFormItems(next);
  };

  // Calculations for Create Modal
  const calculatedSubtotal = formItems.reduce((acc, itm) => {
    const q = Number(itm.quantity) || 0;
    const p = Number(itm.unit_price) || 0;
    return acc + q * p;
  }, 0);

  const calculatedTax = (calculatedSubtotal * (Number(formTaxRate) || 0)) / 100;
  const calculatedTotal = Math.max(
    0,
    calculatedSubtotal + calculatedTax - (Number(formDiscount) || 0)
  );

  // Submit Create Invoice
  const handleCreateInvoice = async (e) => {
    e.preventDefault();
    if (formItems.some((itm) => !itm.description.trim())) {
      alert("Please provide descriptions for all line items.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        customer_id: formCustomerId || null,
        customer_name: !formCustomerId ? formCustomName : null,
        customer_email: !formCustomerId ? formCustomEmail : null,
        issue_date: formIssueDate,
        due_date: formDueDate,
        tax_rate: Number(formTaxRate) || 0,
        discount_amount: Number(formDiscount) || 0,
        notes: formNotes,
        status: formStatus,
        auto_generate_pdf: true,
        items: formItems.map((itm) => ({
          description: itm.description,
          quantity: Number(itm.quantity) || 1,
          unit_price: Number(itm.unit_price) || 0,
        })),
      };

      const res = await fetch(`${API}/billing/invoices`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        showToast("Invoice created and PDF generated successfully!");
        setShowCreateModal(false);
        // Reset form
        setFormItems([{ description: "", quantity: 1, unit_price: 0 }]);
        setFormNotes("");
        setFormCustomerId("");
        setFormCustomName("");
        setFormCustomEmail("");
        fetchData();
      } else {
        const errData = await res.json();
        alert(errData.detail || "Failed to create invoice.");
      }
    } catch (err) {
      console.error(err);
      alert("Error submitting invoice.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="billing-container">
      {/* ── Top Header ── */}
      <div className="billing-header">
        <div className="billing-title-group">
          <h1>
            <FileText size={24} color="#10b981" />
            Billing & Invoicing
          </h1>
          <p>
            Create invoices, track customer payment statuses, generate PDFs, and run automated reminder schedules.
          </p>
        </div>

        <div className="billing-actions">
          <button
            className="btn-secondary"
            onClick={handleTriggerScanner}
            title="Scan for overdue invoices and mark them"
          >
            <Zap size={14} color="#10b981" />
            Run Overdue Check
          </button>
          <button className="btn-secondary" onClick={fetchData} title="Refresh data">
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            Refresh
          </button>
          <button className="btn-emerald" onClick={() => setShowCreateModal(true)}>
            <Plus size={16} />
            Create Invoice
          </button>
        </div>
      </div>

      {/* ── KPI Cards ── */}
      <div className="billing-kpi-grid">
        <div className="billing-kpi-card">
          <div className="billing-kpi-icon-wrap kpi-icon-green">
            <DollarSign size={22} />
          </div>
          <div className="billing-kpi-info">
            <span className="billing-kpi-label">Total Revenue</span>
            <span className="billing-kpi-value emerald">
              ${(stats?.total_revenue ?? 0).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
            <span className="billing-kpi-sub">
              {stats?.paid_invoices ?? 0} paid invoices
            </span>
          </div>
        </div>

        <div className="billing-kpi-card">
          <div className="billing-kpi-icon-wrap kpi-icon-amber">
            <Clock size={22} />
          </div>
          <div className="billing-kpi-info">
            <span className="billing-kpi-label">Pending Amount</span>
            <span className="billing-kpi-value">
              ${(stats?.pending_amount ?? 0).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
            <span className="billing-kpi-sub">
              {stats?.pending_invoices ?? 0} awaiting payment
            </span>
          </div>
        </div>

        <div className="billing-kpi-card">
          <div className="billing-kpi-icon-wrap kpi-icon-red">
            <AlertTriangle size={22} />
          </div>
          <div className="billing-kpi-info">
            <span className="billing-kpi-label">Overdue Invoices</span>
            <span className="billing-kpi-value" style={{ color: "#ef4444" }}>
              ${(stats?.overdue_amount ?? 0).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
            <span className="billing-kpi-sub">
              {stats?.overdue_invoices ?? 0} overdue accounts
            </span>
          </div>
        </div>

        <div className="billing-kpi-card">
          <div className="billing-kpi-icon-wrap kpi-icon-slate">
            <FileText size={22} />
          </div>
          <div className="billing-kpi-info">
            <span className="billing-kpi-label">Total Invoices</span>
            <span className="billing-kpi-value">
              {stats?.total_invoices ?? 0}
            </span>
            <span className="billing-kpi-sub">Lifetime generated</span>
          </div>
        </div>
      </div>

      {/* ── Controls: Filter Tabs & Search ── */}
      <div className="billing-controls">
        <div className="billing-filter-tabs">
          {["all", "pending", "paid", "overdue", "draft", "cancelled"].map(
            (flt) => (
              <button
                key={flt}
                className={`filter-tab-btn ${
                  activeFilter === flt ? "active" : ""
                }`}
                onClick={() => setActiveFilter(flt)}
              >
                {flt.toUpperCase()}
              </button>
            )
          )}
        </div>

        <form className="billing-search-box" onSubmit={handleSearchSubmit}>
          <Search size={14} color="#64748b" />
          <input
            type="text"
            placeholder="Search invoice # or customer..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </form>
      </div>

      {/* ── Invoices Table ── */}
      <div className="billing-table-card">
        {loading && invoices.length === 0 ? (
          <div className="billing-empty-state">
            <RefreshCw size={24} className="spin" color="#10b981" />
            <p style={{ marginTop: 12 }}>Loading invoices...</p>
          </div>
        ) : invoices.length === 0 ? (
          <div className="billing-empty-state">
            <FileText size={36} color="#10b981" />
            <h3>No Invoices Found</h3>
            <p>
              {activeFilter !== "all"
                ? `No invoices with status '${activeFilter}'.`
                : "Get started by generating your first customer invoice."}
            </p>
            <button
              className="btn-emerald"
              style={{ marginTop: 16 }}
              onClick={() => setShowCreateModal(true)}
            >
              <Plus size={14} /> Create Invoice
            </button>
          </div>
        ) : (
          <table className="billing-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Customer</th>
                <th>Issue Date</th>
                <th>Due Date</th>
                <th>Items</th>
                <th>Total</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id}>
                  <td>
                    <span
                      className="invoice-num-cell"
                      onClick={() => handleViewInvoice(inv.id)}
                    >
                      {inv.invoice_number}
                    </span>
                  </td>
                  <td>
                    <div className="customer-cell-name">
                      {inv.customer_name}
                    </div>
                    {inv.customer_email && (
                      <div className="customer-cell-email">
                        {inv.customer_email}
                      </div>
                    )}
                  </td>
                  <td>{inv.issue_date}</td>
                  <td>{inv.due_date}</td>
                  <td>{inv.items_count} item(s)</td>
                  <td style={{ fontWeight: 700, color: "#ffffff" }}>
                    ${(inv.total_amount ?? 0).toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </td>
                  <td>
                    <span className={`status-pill status-${inv.status}`}>
                      ● {inv.status}
                    </span>
                  </td>
                  <td>
                    <div className="row-actions">
                      <button
                        className="icon-action-btn"
                        title="View Details"
                        onClick={() => handleViewInvoice(inv.id)}
                      >
                        <Eye size={14} />
                      </button>
                      <button
                        className="icon-action-btn"
                        title="Download / View PDF"
                        onClick={() => handleDownloadPdf(inv.id)}
                      >
                        <Download size={14} />
                      </button>
                      {inv.status !== "paid" && (
                        <button
                          className="icon-action-btn"
                          title="Mark as Paid"
                          onClick={() => handleMarkAsPaid(inv.id)}
                        >
                          <CheckCircle size={14} color="#10b981" />
                        </button>
                      )}
                      <button
                        className="icon-action-btn delete"
                        title="Delete Invoice"
                        onClick={() => handleDeleteInvoice(inv.id)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ── CREATE INVOICE MODAL ── */}
      {showCreateModal && (
        <div className="billing-modal-overlay">
          <div className="billing-modal">
            <div className="billing-modal-header">
              <h2>Create New Invoice</h2>
              <button
                className="billing-modal-close"
                onClick={() => setShowCreateModal(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateInvoice}>
              <div className="billing-modal-body">
                {/* Customer selection */}
                <div className="form-group">
                  <label>Select Customer</label>
                  <select
                    className="form-select"
                    value={formCustomerId}
                    onChange={(e) => setFormCustomerId(e.target.value)}
                  >
                    <option value="">-- Enter Custom / Unregistered --</option>
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} {c.company ? `(${c.company})` : ""}
                      </option>
                    ))}
                  </select>
                </div>

                {!formCustomerId && (
                  <div className="form-group-row">
                    <div className="form-group">
                      <label>Customer Name *</label>
                      <input
                        className="form-input"
                        type="text"
                        required
                        placeholder="e.g. Acme Innovations"
                        value={formCustomName}
                        onChange={(e) => setFormCustomName(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label>Customer Email</label>
                      <input
                        className="form-input"
                        type="email"
                        placeholder="billing@acme.com"
                        value={formCustomEmail}
                        onChange={(e) => setFormCustomEmail(e.target.value)}
                      />
                    </div>
                  </div>
                )}

                {/* Dates */}
                <div className="form-group-row">
                  <div className="form-group">
                    <label>Issue Date</label>
                    <input
                      className="form-input"
                      type="date"
                      value={formIssueDate}
                      onChange={(e) => setFormIssueDate(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Due Date</label>
                    <input
                      className="form-input"
                      type="date"
                      value={formDueDate}
                      onChange={(e) => setFormDueDate(e.target.value)}
                    />
                  </div>
                </div>

                {/* Line Items Builder */}
                <div className="modal-items-box">
                  <div className="items-box-title">
                    <span>Line Items</span>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: "4px 8px", fontSize: 11 }}
                      onClick={handleAddItemRow}
                    >
                      <Plus size={12} /> Add Item
                    </button>
                  </div>

                  {formItems.map((itm, i) => (
                    <div key={i} className="line-item-row">
                      <input
                        className="form-input"
                        type="text"
                        required
                        placeholder="Item / service description"
                        value={itm.description}
                        onChange={(e) =>
                          handleItemChange(i, "description", e.target.value)
                        }
                      />
                      <input
                        className="form-input"
                        type="number"
                        min="1"
                        placeholder="Qty"
                        value={itm.quantity}
                        onChange={(e) =>
                          handleItemChange(i, "quantity", e.target.value)
                        }
                      />
                      <input
                        className="form-input"
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="Unit $"
                        value={itm.unit_price}
                        onChange={(e) =>
                          handleItemChange(i, "unit_price", e.target.value)
                        }
                      />
                      <div className="line-total-preview">
                        $
                        {(
                          (Number(itm.quantity) || 0) *
                          (Number(itm.unit_price) || 0)
                        ).toFixed(2)}
                      </div>
                      <button
                        type="button"
                        className="icon-action-btn delete"
                        onClick={() => handleRemoveItemRow(i)}
                        disabled={formItems.length === 1}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>

                {/* Tax & Discount */}
                <div className="form-group-row">
                  <div className="form-group">
                    <label>Tax Rate (%)</label>
                    <input
                      className="form-input"
                      type="number"
                      min="0"
                      step="0.1"
                      value={formTaxRate}
                      onChange={(e) => setFormTaxRate(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Discount ($)</label>
                    <input
                      className="form-input"
                      type="number"
                      min="0"
                      step="0.01"
                      value={formDiscount}
                      onChange={(e) => setFormDiscount(e.target.value)}
                    />
                  </div>
                </div>

                {/* Status & Notes */}
                <div className="form-group-row">
                  <div className="form-group">
                    <label>Initial Status</label>
                    <select
                      className="form-select"
                      value={formStatus}
                      onChange={(e) => setFormStatus(e.target.value)}
                    >
                      <option value="pending">Pending</option>
                      <option value="draft">Draft</option>
                      <option value="paid">Paid</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Payment Notes / Instructions</label>
                    <input
                      className="form-input"
                      type="text"
                      placeholder="e.g. Wire transfer info or PO number"
                      value={formNotes}
                      onChange={(e) => setFormNotes(e.target.value)}
                    />
                  </div>
                </div>

                {/* Live Total Box */}
                <div className="modal-summary-box">
                  <div className="summary-row">
                    <span>Subtotal:</span>
                    <span>${calculatedSubtotal.toFixed(2)}</span>
                  </div>
                  <div className="summary-row">
                    <span>Tax ({formTaxRate}%):</span>
                    <span>${calculatedTax.toFixed(2)}</span>
                  </div>
                  {Number(formDiscount) > 0 && (
                    <div className="summary-row">
                      <span>Discount:</span>
                      <span>-${Number(formDiscount).toFixed(2)}</span>
                    </div>
                  )}
                  <div className="summary-row grand-total">
                    <span>Total Amount:</span>
                    <span>${calculatedTotal.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              <div className="billing-modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-emerald"
                  disabled={submitting}
                >
                  {submitting ? "Generating PDF & Saving..." : "Create & Generate PDF"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── INVOICE DETAIL MODAL ── */}
      {selectedInvoice && (
        <div className="billing-modal-overlay">
          <div className="billing-modal">
            <div className="billing-modal-header">
              <h2>Invoice: {selectedInvoice.invoice_number}</h2>
              <button
                className="billing-modal-close"
                onClick={() => setSelectedInvoice(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="billing-modal-body">
              {/* Meta Grid */}
              <div className="detail-meta-grid">
                <div>
                  <div className="detail-label">Billed To</div>
                  <div className="detail-val">
                    {selectedInvoice.customer?.name || "Direct Customer"}
                  </div>
                  <div style={{ fontSize: 12, color: "#94a3b8" }}>
                    {selectedInvoice.customer?.email || ""}
                  </div>
                </div>
                <div>
                  <div className="detail-label">Status</div>
                  <div style={{ marginTop: 4 }}>
                    <span
                      className={`status-pill status-${selectedInvoice.status}`}
                    >
                      ● {selectedInvoice.status}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="detail-label">Issue Date</div>
                  <div className="detail-val">{selectedInvoice.issue_date}</div>
                </div>
                <div>
                  <div className="detail-label">Due Date</div>
                  <div className="detail-val">{selectedInvoice.due_date}</div>
                </div>
              </div>

              {/* Items List */}
              <div className="modal-items-box">
                <div className="items-box-title">
                  <span>Line Items</span>
                </div>
                <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ color: "#94a3b8", textAlign: "left", borderBottom: "1px solid #1e293b" }}>
                      <th style={{ padding: "6px 0" }}>Description</th>
                      <th style={{ padding: "6px 0", textAlign: "center" }}>Qty</th>
                      <th style={{ padding: "6px 0", textAlign: "right" }}>Unit Price</th>
                      <th style={{ padding: "6px 0", textAlign: "right" }}>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(selectedInvoice.items || []).map((itm) => (
                      <tr key={itm.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "8px 0", color: "#f1f5f9" }}>{itm.description}</td>
                        <td style={{ padding: "8px 0", textAlign: "center" }}>{itm.quantity}</td>
                        <td style={{ padding: "8px 0", textAlign: "right" }}>${floatVal(itm.unit_price)}</td>
                        <td style={{ padding: "8px 0", textAlign: "right", fontWeight: 700, color: "#ffffff" }}>
                          ${floatVal(itm.total_amount)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Totals Summary */}
              <div className="modal-summary-box">
                <div className="summary-row">
                  <span>Subtotal:</span>
                  <span>${floatVal(selectedInvoice.subtotal)}</span>
                </div>
                <div className="summary-row">
                  <span>Tax:</span>
                  <span>${floatVal(selectedInvoice.tax_amount)}</span>
                </div>
                {floatVal(selectedInvoice.discount_amount) > 0 && (
                  <div className="summary-row">
                    <span>Discount:</span>
                    <span>-${floatVal(selectedInvoice.discount_amount)}</span>
                  </div>
                )}
                <div className="summary-row grand-total">
                  <span>Total Amount Due:</span>
                  <span>${floatVal(selectedInvoice.total_amount)}</span>
                </div>
              </div>

              {selectedInvoice.notes && (
                <div style={{ fontSize: 12, color: "#94a3b8" }}>
                  <strong style={{ color: "#ffffff" }}>Notes: </strong>
                  {selectedInvoice.notes}
                </div>
              )}
            </div>

            <div className="billing-modal-footer">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => handleDownloadPdf(selectedInvoice.id)}
              >
                <Download size={14} color="#10b981" /> Download PDF
              </button>
              {selectedInvoice.status !== "paid" && (
                <button
                  type="button"
                  className="btn-emerald"
                  onClick={() => handleMarkAsPaid(selectedInvoice.id)}
                >
                  <Check size={14} /> Mark as Paid
                </button>
              )}
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setSelectedInvoice(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toastMessage && (
        <div
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            background: "#10b981",
            color: "#ffffff",
            padding: "12px 20px",
            borderRadius: 8,
            fontWeight: 600,
            fontSize: 13,
            boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
            zIndex: 9999,
          }}
        >
          {toastMessage}
        </div>
      )}
    </div>
  );
}

function floatVal(val) {
  const n = parseFloat(val);
  return isNaN(n) ? "0.00" : n.toFixed(2);
}
