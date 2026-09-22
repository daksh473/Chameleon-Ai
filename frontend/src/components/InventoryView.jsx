import { useState, useEffect } from "react";
import {
  Package,
  ShoppingCart,
  AlertTriangle,
  DollarSign,
  Plus,
  RefreshCw,
  Search,
  CheckCircle,
  X,
  Edit2,
  Trash2,
  FileText,
  Sliders,
  TrendingDown,
  Eye,
  Check,
} from "lucide-react";
import "./InventoryView.css";

const API = "http://localhost:8000";

export default function InventoryView() {
  const [activeTab, setActiveTab] = useState("products"); // 'products' | 'orders' | 'alerts'
  const [stats, setStats] = useState(null);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [orderStatusFilter, setOrderStatusFilter] = useState("all");

  // Modals
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [showStockModal, setShowStockModal] = useState(false);
  const [selectedStockProduct, setSelectedStockProduct] = useState(null);
  const [stockDelta, setStockDelta] = useState(0);

  const [showOrderModal, setShowOrderModal] = useState(false);
  const [selectedOrderDetail, setSelectedOrderDetail] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Form states
  const [prodName, setProdName] = useState("");
  const [prodSku, setProdSku] = useState("");
  const [prodDesc, setProdDesc] = useState("");
  const [prodUnitPrice, setProdUnitPrice] = useState(0);
  const [prodCostPrice, setProdCostPrice] = useState(0);
  const [prodStock, setProdStock] = useState(0);
  const [prodMinStock, setProdMinStock] = useState(10);
  const [prodCategory, setProdCategory] = useState("General");

  // Order Form
  const [orderCustomerId, setOrderCustomerId] = useState("");
  const [orderCustomerName, setOrderCustomerName] = useState("");
  const [orderNotes, setOrderNotes] = useState("");
  const [orderItems, setOrderItems] = useState([
    { product_id: "", quantity: 1, unit_price: 0 },
  ]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [stRes, prRes, orRes, cuRes] = await Promise.all([
        fetch(`${API}/inventory/stats`).then((r) => (r.ok ? r.json() : null)),
        fetch(
          `${API}/inventory/products?category=${categoryFilter}&search=${encodeURIComponent(
            searchQuery
          )}`
        ).then((r) => (r.ok ? r.json() : { products: [] })),
        fetch(
          `${API}/inventory/orders?status=${orderStatusFilter}`
        ).then((r) => (r.ok ? r.json() : { orders: [] })),
        fetch(`${API}/crm/customers`).then((r) => (r.ok ? r.json() : [])),
      ]);

      setStats(stRes);
      setProducts(prRes.products || []);
      setOrders(orRes.orders || []);
      setCustomers(Array.isArray(cuRes) ? cuRes : []);
    } catch (err) {
      console.error("Inventory fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [categoryFilter, orderStatusFilter]);

  // Product CRUD
  const handleOpenCreateProduct = () => {
    setEditingProduct(null);
    setProdName("");
    setProdSku("");
    setProdDesc("");
    setProdUnitPrice(0);
    setProdCostPrice(0);
    setProdStock(10);
    setProdMinStock(5);
    setProdCategory("General");
    setShowProductModal(true);
  };

  const handleOpenEditProduct = (p) => {
    setEditingProduct(p);
    setProdName(p.name);
    setProdSku(p.sku);
    setProdDesc(p.description || "");
    setProdUnitPrice(p.unit_price);
    setProdCostPrice(p.cost_price);
    setProdStock(p.stock_quantity);
    setProdMinStock(p.min_stock_threshold);
    setProdCategory(p.category || "General");
    setShowProductModal(true);
  };

  const handleSaveProduct = async (e) => {
    e.preventDefault();
    try {
      if (editingProduct) {
        // Update
        const res = await fetch(`${API}/inventory/products/${editingProduct.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: prodName,
            description: prodDesc,
            unit_price: Number(prodUnitPrice),
            cost_price: Number(prodCostPrice),
            min_stock_threshold: Number(prodMinStock),
            category: prodCategory,
          }),
        });
        if (res.ok) {
          showToast("Product updated successfully.");
          setShowProductModal(false);
          fetchData();
        }
      } else {
        // Create
        const res = await fetch(`${API}/inventory/products`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: prodName,
            sku: prodSku || null,
            description: prodDesc,
            unit_price: Number(prodUnitPrice),
            cost_price: Number(prodCostPrice),
            stock_quantity: Number(prodStock),
            min_stock_threshold: Number(prodMinStock),
            category: prodCategory,
          }),
        });
        if (res.ok) {
          showToast("Product created successfully!");
          setShowProductModal(false);
          fetchData();
        } else {
          const err = await res.json();
          alert(err.detail || "Failed to create product.");
        }
      }
    } catch (err) {
      alert("Error saving product.");
    }
  };

  // Stock Adjustment
  const handleOpenStockAdjust = (p) => {
    setSelectedStockProduct(p);
    setStockDelta(0);
    setShowStockModal(true);
  };

  const handleSaveStockAdjust = async () => {
    if (!selectedStockProduct) return;
    try {
      const res = await fetch(
        `${API}/inventory/products/${selectedStockProduct.id}/adjust-stock`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ delta: Number(stockDelta) }),
        }
      );
      if (res.ok) {
        showToast("Stock quantity adjusted.");
        setShowStockModal(false);
        fetchData();
      }
    } catch (err) {
      showToast("Failed to adjust stock.");
    }
  };

  // Order Fulfillment
  const handleFulfillOrder = async (orderId) => {
    try {
      const res = await fetch(`${API}/inventory/orders/${orderId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "fulfilled" }),
      });
      if (res.ok) {
        showToast("Order FULFILLED! Inventory stock decremented automatically.");
        fetchData();
        if (selectedOrderDetail?.id === orderId) {
          const updated = await fetch(`${API}/inventory/orders/${orderId}`).then(
            (r) => r.json()
          );
          setSelectedOrderDetail(updated);
        }
      }
    } catch (err) {
      showToast("Failed to fulfill order.");
    }
  };

  // Convert Order to Invoice
  const handleConvertToInvoice = async (orderId) => {
    try {
      const res = await fetch(
        `${API}/inventory/orders/${orderId}/convert-to-invoice?tax_rate=10`,
        { method: "POST" }
      );
      if (res.ok) {
        const data = await res.json();
        showToast(`Converted to Invoice ${data.invoice_number}! PDF generated.`);
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to convert to invoice.");
      }
    } catch (err) {
      showToast("Error converting to invoice.");
    }
  };

  // Order Detail
  const handleViewOrderDetail = async (orderId) => {
    try {
      const res = await fetch(`${API}/inventory/orders/${orderId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedOrderDetail(data);
      }
    } catch (err) {
      showToast("Failed to load order details.");
    }
  };

  // Create Order Form
  const handleAddOrderItem = () => {
    setOrderItems([...orderItems, { product_id: "", quantity: 1, unit_price: 0 }]);
  };

  const handleRemoveOrderItem = (idx) => {
    if (orderItems.length === 1) return;
    setOrderItems(orderItems.filter((_, i) => i !== idx));
  };

  const handleOrderItemChange = (idx, field, val) => {
    const next = [...orderItems];
    next[idx][field] = val;
    if (field === "product_id") {
      const prod = products.find((p) => p.id === val);
      if (prod) {
        next[idx].unit_price = prod.unit_price;
      }
    }
    setOrderItems(next);
  };

  const calculatedOrderTotal = orderItems.reduce((acc, itm) => {
    return acc + (Number(itm.quantity) || 0) * (Number(itm.unit_price) || 0);
  }, 0);

  const handleCreateOrder = async (e) => {
    e.preventDefault();
    if (orderItems.some((itm) => !itm.product_id)) {
      alert("Please select a product for all order items.");
      return;
    }
    try {
      const payload = {
        customer_id: orderCustomerId || null,
        customer_name: !orderCustomerId ? orderCustomerName : null,
        notes: orderNotes,
        status: "pending",
        items: orderItems.map((itm) => ({
          product_id: itm.product_id,
          quantity: Number(itm.quantity) || 1,
          unit_price: Number(itm.unit_price) || 0,
        })),
      };
      const res = await fetch(`${API}/inventory/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        showToast("Sales order created successfully!");
        setShowOrderModal(false);
        setOrderItems([{ product_id: "", quantity: 1, unit_price: 0 }]);
        setOrderNotes("");
        setOrderCustomerId("");
        setOrderCustomerName("");
        fetchData();
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to create order.");
      }
    } catch (err) {
      alert("Error submitting order.");
    }
  };

  const categoriesList = [
    "all",
    ...Array.from(new Set(products.map((p) => p.category).filter(Boolean))),
  ];

  const lowStockProducts = products.filter(
    (p) => p.stock_quantity <= p.min_stock_threshold
  );

  return (
    <div className="inventory-container">
      {/* ── Top Header ── */}
      <div className="inventory-header">
        <div className="inventory-title-group">
          <h1>
            <Package size={24} color="#10b981" />
            Inventory & Fulfillment
          </h1>
          <p>
            Catalog management, stock level monitoring, sales orders, and automatic stock decrement on fulfillment.
          </p>
        </div>

        <div className="inventory-actions">
          <button className="btn-secondary" onClick={fetchData} title="Refresh data">
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            Refresh
          </button>
          <button
            className="btn-secondary"
            onClick={() => setShowOrderModal(true)}
          >
            <ShoppingCart size={15} color="#10b981" />
            New Sales Order
          </button>
          <button className="btn-emerald" onClick={handleOpenCreateProduct}>
            <Plus size={16} />
            Add Product
          </button>
        </div>
      </div>

      {/* ── KPI Cards ── */}
      <div className="inventory-kpi-grid">
        <div className="inventory-kpi-card">
          <div className="inventory-kpi-icon-wrap kpi-icon-green">
            <Package size={22} />
          </div>
          <div className="inventory-kpi-info">
            <span className="inventory-kpi-label">Active Products</span>
            <span className="inventory-kpi-value emerald">
              {stats?.total_products ?? 0}
            </span>
            <span className="inventory-kpi-sub">In Catalog</span>
          </div>
        </div>

        <div className="inventory-kpi-card">
          <div className="inventory-kpi-icon-wrap kpi-icon-emerald">
            <DollarSign size={22} />
          </div>
          <div className="inventory-kpi-info">
            <span className="inventory-kpi-label">Inventory Valuation</span>
            <span className="inventory-kpi-value">
              ${(stats?.total_inventory_value ?? 0).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
            <span className="inventory-kpi-sub">Selling retail asset value</span>
          </div>
        </div>

        <div className="inventory-kpi-card">
          <div className="inventory-kpi-icon-wrap kpi-icon-red">
            <AlertTriangle size={22} />
          </div>
          <div className="inventory-kpi-info">
            <span className="inventory-kpi-label">Low Stock Alerts</span>
            <span className="inventory-kpi-value" style={{ color: "#ef4444" }}>
              {stats?.low_stock_items ?? 0}
            </span>
            <span className="inventory-kpi-sub">At or below threshold</span>
          </div>
        </div>

        <div className="inventory-kpi-card">
          <div className="inventory-kpi-icon-wrap kpi-icon-amber">
            <ShoppingCart size={22} />
          </div>
          <div className="inventory-kpi-info">
            <span className="inventory-kpi-label">Fulfilled Orders</span>
            <span className="inventory-kpi-value">
              {stats?.fulfilled_orders ?? 0} / {stats?.total_orders ?? 0}
            </span>
            <span className="inventory-kpi-sub">
              ${(stats?.total_fulfilled_revenue ?? 0).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })} revenue
            </span>
          </div>
        </div>
      </div>

      {/* ── Navigation Tabs ── */}
      <div className="inventory-nav-tabs">
        <button
          className={`inventory-nav-tab ${activeTab === "products" ? "active" : ""}`}
          onClick={() => setActiveTab("products")}
        >
          <Package size={15} />
          Products Catalog ({products.length})
        </button>
        <button
          className={`inventory-nav-tab ${activeTab === "orders" ? "active" : ""}`}
          onClick={() => setActiveTab("orders")}
        >
          <ShoppingCart size={15} />
          Orders & Fulfillment ({orders.length})
        </button>
        <button
          className={`inventory-nav-tab ${activeTab === "alerts" ? "active" : ""}`}
          onClick={() => setActiveTab("alerts")}
        >
          <AlertTriangle size={15} />
          Low Stock Alerts
          {stats?.low_stock_items > 0 && (
            <span className="tab-badge">{stats.low_stock_items}</span>
          )}
        </button>
      </div>

      {/* ════════ TAB 1: PRODUCTS CATALOG ════════ */}
      {activeTab === "products" && (
        <>
          <div className="inventory-controls">
            <div className="inventory-search-box">
              <Search size={14} color="#64748b" />
              <input
                type="text"
                placeholder="Search products by name or SKU..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchData()}
              />
            </div>

            <div className="inventory-filter-group">
              <select
                className="form-select"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                {categoriesList.map((c) => (
                  <option key={c} value={c}>
                    {c.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="inventory-table-card">
            {products.length === 0 ? (
              <div className="billing-empty-state">
                <Package size={36} color="#10b981" />
                <h3>No Products Found</h3>
                <p>Add your first catalog product to start tracking inventory.</p>
                <button
                  className="btn-emerald"
                  style={{ marginTop: 16 }}
                  onClick={handleOpenCreateProduct}
                >
                  <Plus size={14} /> Add Product
                </button>
              </div>
            ) : (
              <table className="inventory-table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Product Name</th>
                    <th>Category</th>
                    <th>Unit Price</th>
                    <th>Cost</th>
                    <th>Stock Level</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((p) => {
                    const ratio =
                      p.min_stock_threshold > 0
                        ? Math.min(100, Math.round((p.stock_quantity / (p.min_stock_threshold * 2)) * 100))
                        : 100;
                    const barClass =
                      p.stock_quantity === 0
                        ? "empty"
                        : p.is_low_stock
                        ? "low"
                        : "normal";

                    return (
                      <tr key={p.id}>
                        <td>
                          <span className="sku-pill">{p.sku}</span>
                        </td>
                        <td>
                          <div style={{ fontWeight: 600, color: "#ffffff" }}>
                            {p.name}
                          </div>
                          {p.description && (
                            <div style={{ fontSize: 11, color: "#64748b" }}>
                              {p.description.slice(0, 50)}
                            </div>
                          )}
                        </td>
                        <td>
                          <span style={{ fontSize: 12, color: "#94a3b8" }}>
                            {p.category}
                          </span>
                        </td>
                        <td style={{ fontWeight: 700, color: "#10b981" }}>
                          ${(p.unit_price ?? 0).toFixed(2)}
                        </td>
                        <td style={{ color: "#94a3b8" }}>
                          ${(p.cost_price ?? 0).toFixed(2)}
                        </td>
                        <td>
                          <div className="stock-bar-wrap">
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                fontSize: 11,
                              }}
                            >
                              <strong style={{ color: "#ffffff" }}>
                                {p.stock_quantity}
                              </strong>
                              <span style={{ color: "#64748b" }}>
                                Min: {p.min_stock_threshold}
                              </span>
                            </div>
                            <div className="stock-bar-track">
                              <div
                                className={`stock-bar-fill ${barClass}`}
                                style={{ width: `${ratio}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td>
                          {p.is_low_stock ? (
                            <span className="status-pill status-overdue">
                              ● LOW STOCK
                            </span>
                          ) : (
                            <span className="status-pill status-fulfilled">
                              ● IN STOCK
                            </span>
                          )}
                        </td>
                        <td>
                          <div className="row-actions">
                            <button
                              className="icon-action-btn"
                              title="Adjust Stock Level"
                              onClick={() => handleOpenStockAdjust(p)}
                            >
                              <Sliders size={13} color="#10b981" />
                            </button>
                            <button
                              className="icon-action-btn"
                              title="Edit Product"
                              onClick={() => handleOpenEditProduct(p)}
                            >
                              <Edit2 size={13} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* ════════ TAB 2: ORDERS & FULFILLMENT ════════ */}
      {activeTab === "orders" && (
        <>
          <div className="inventory-controls">
            <div className="billing-filter-tabs">
              {["all", "pending", "processing", "fulfilled", "cancelled"].map(
                (st) => (
                  <button
                    key={st}
                    className={`filter-tab-btn ${
                      orderStatusFilter === st ? "active" : ""
                    }`}
                    onClick={() => setOrderStatusFilter(st)}
                  >
                    {st.toUpperCase()}
                  </button>
                )
              )}
            </div>

            <button
              className="btn-emerald"
              onClick={() => setShowOrderModal(true)}
            >
              <Plus size={14} /> New Sales Order
            </button>
          </div>

          <div className="inventory-table-card">
            {orders.length === 0 ? (
              <div className="billing-empty-state">
                <ShoppingCart size={36} color="#10b981" />
                <h3>No Orders Found</h3>
                <p>Create a sales order to fulfill items and decrement stock automatically.</p>
              </div>
            ) : (
              <table className="inventory-table">
                <thead>
                  <tr>
                    <th>Order #</th>
                    <th>Customer</th>
                    <th>Items Count</th>
                    <th>Total Amount</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((o) => (
                    <tr key={o.id}>
                      <td style={{ fontFamily: "monospace", fontWeight: 700, color: "#10b981" }}>
                        {o.order_number}
                      </td>
                      <td style={{ fontWeight: 600, color: "#ffffff" }}>
                        {o.customer_name}
                      </td>
                      <td>{o.items_count} item(s)</td>
                      <td style={{ fontWeight: 700, color: "#ffffff" }}>
                        ${(o.total_amount ?? 0).toFixed(2)}
                      </td>
                      <td style={{ color: "#64748b", fontSize: 12 }}>
                        {o.created_at ? o.created_at.slice(0, 10) : "-"}
                      </td>
                      <td>
                        <span className={`status-pill status-${o.status}`}>
                          ● {o.status}
                        </span>
                      </td>
                      <td>
                        <div className="row-actions">
                          <button
                            className="icon-action-btn"
                            title="View Order Details"
                            onClick={() => handleViewOrderDetail(o.id)}
                          >
                            <Eye size={14} />
                          </button>
                          {o.status !== "fulfilled" && (
                            <button
                              className="icon-action-btn"
                              title="Fulfill Order (Auto-Decrements Stock)"
                              onClick={() => handleFulfillOrder(o.id)}
                            >
                              <CheckCircle size={14} color="#10b981" />
                            </button>
                          )}
                          <button
                            className="icon-action-btn"
                            title="Convert to Billing Invoice"
                            onClick={() => handleConvertToInvoice(o.id)}
                          >
                            <FileText size={14} color="#10b981" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* ════════ TAB 3: LOW STOCK ALERTS ════════ */}
      {activeTab === "alerts" && (
        <div className="inventory-table-card">
          {lowStockProducts.length === 0 ? (
            <div className="billing-empty-state">
              <CheckCircle size={36} color="#10b981" />
              <h3>All Stock Levels Healthy!</h3>
              <p>No products are currently at or below their minimum reorder thresholds.</p>
            </div>
          ) : (
            <table className="inventory-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Category</th>
                  <th>On-Hand Stock</th>
                  <th>Min Threshold</th>
                  <th>Deficit</th>
                  <th>Quick Action</th>
                </tr>
              </thead>
              <tbody>
                {lowStockProducts.map((p) => {
                  const deficit = Math.max(0, p.min_stock_threshold - p.stock_quantity);
                  return (
                    <tr key={p.id}>
                      <td>
                        <span className="sku-pill">{p.sku}</span>
                      </td>
                      <td style={{ fontWeight: 600, color: "#ffffff" }}>
                        {p.name}
                      </td>
                      <td>{p.category}</td>
                      <td style={{ fontWeight: 800, color: "#ef4444" }}>
                        {p.stock_quantity}
                      </td>
                      <td>{p.min_stock_threshold}</td>
                      <td>
                        <span style={{ color: "#f59e0b", fontWeight: 700 }}>
                          +{deficit} needed
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn-secondary"
                          style={{ padding: "4px 10px", fontSize: 12 }}
                          onClick={() => handleOpenStockAdjust(p)}
                        >
                          <Plus size={12} color="#10b981" /> Restock
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── CREATE / EDIT PRODUCT MODAL ── */}
      {showProductModal && (
        <div className="inventory-modal-overlay">
          <div className="inventory-modal">
            <div className="inventory-modal-header">
              <h2>{editingProduct ? "Edit Product" : "Add Catalog Product"}</h2>
              <button
                className="inventory-modal-close"
                onClick={() => setShowProductModal(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveProduct}>
              <div className="inventory-modal-body">
                <div className="form-group-row">
                  <div className="form-group">
                    <label>Product Name *</label>
                    <input
                      className="form-input"
                      type="text"
                      required
                      placeholder="e.g. Chameleon Core Sensor"
                      value={prodName}
                      onChange={(e) => setProdName(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>SKU (Leave blank to auto-generate)</label>
                    <input
                      className="form-input"
                      type="text"
                      placeholder="Auto (e.g. PRD-0001)"
                      value={prodSku}
                      disabled={!!editingProduct}
                      onChange={(e) => setProdSku(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    placeholder="Product specs and notes..."
                    value={prodDesc}
                    onChange={(e) => setProdDesc(e.target.value)}
                  />
                </div>

                <div className="form-group-row">
                  <div className="form-group">
                    <label>Unit Selling Price ($) *</label>
                    <input
                      className="form-input"
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      value={prodUnitPrice}
                      onChange={(e) => setProdUnitPrice(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Unit Cost Price ($)</label>
                    <input
                      className="form-input"
                      type="number"
                      step="0.01"
                      min="0"
                      value={prodCostPrice}
                      onChange={(e) => setProdCostPrice(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group-row">
                  {!editingProduct && (
                    <div className="form-group">
                      <label>Initial Stock Quantity</label>
                      <input
                        className="form-input"
                        type="number"
                        min="0"
                        value={prodStock}
                        onChange={(e) => setProdStock(e.target.value)}
                      />
                    </div>
                  )}
                  <div className="form-group">
                    <label>Low Stock Alert Threshold</label>
                    <input
                      className="form-input"
                      type="number"
                      min="0"
                      value={prodMinStock}
                      onChange={(e) => setProdMinStock(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Category</label>
                    <input
                      className="form-input"
                      type="text"
                      placeholder="Hardware, SaaS, etc."
                      value={prodCategory}
                      onChange={(e) => setProdCategory(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className="inventory-modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowProductModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-emerald">
                  {editingProduct ? "Save Changes" : "Create Product"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── QUICK STOCK ADJUSTMENT MODAL ── */}
      {showStockModal && selectedStockProduct && (
        <div className="inventory-modal-overlay">
          <div className="inventory-modal" style={{ maxWidth: 440 }}>
            <div className="inventory-modal-header">
              <h2>Adjust Stock: {selectedStockProduct.name}</h2>
              <button
                className="inventory-modal-close"
                onClick={() => setShowStockModal(false)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="inventory-modal-body">
              <div style={{ fontSize: 13, color: "#94a3b8" }}>
                Current Stock:{" "}
                <strong style={{ color: "#10b981", fontSize: 16 }}>
                  {selectedStockProduct.stock_quantity}
                </strong>{" "}
                units
              </div>

              <div className="form-group">
                <label>Add or Deduct Stock (Delta)</label>
                <input
                  className="form-input"
                  type="number"
                  placeholder="+10 or -5"
                  value={stockDelta}
                  onChange={(e) => setStockDelta(e.target.value)}
                />
              </div>

              <div style={{ fontSize: 12, color: "#64748b" }}>
                New Stock Level Preview:{" "}
                <strong style={{ color: "#ffffff" }}>
                  {Math.max(
                    0,
                    selectedStockProduct.stock_quantity + (Number(stockDelta) || 0)
                  )}
                </strong>
              </div>
            </div>

            <div className="inventory-modal-footer">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setShowStockModal(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-emerald"
                onClick={handleSaveStockAdjust}
              >
                Update Stock
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── CREATE SALES ORDER MODAL ── */}
      {showOrderModal && (
        <div className="inventory-modal-overlay">
          <div className="inventory-modal" style={{ maxWidth: 680 }}>
            <div className="inventory-modal-header">
              <h2>Create Sales Order</h2>
              <button
                className="inventory-modal-close"
                onClick={() => setShowOrderModal(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateOrder}>
              <div className="inventory-modal-body">
                <div className="form-group">
                  <label>Select Customer</label>
                  <select
                    className="form-select"
                    value={orderCustomerId}
                    onChange={(e) => setOrderCustomerId(e.target.value)}
                  >
                    <option value="">-- Custom / Direct Customer --</option>
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} {c.company ? `(${c.company})` : ""}
                      </option>
                    ))}
                  </select>
                </div>

                {!orderCustomerId && (
                  <div className="form-group">
                    <label>Customer Name *</label>
                    <input
                      className="form-input"
                      type="text"
                      required
                      placeholder="e.g. Horizon Labs"
                      value={orderCustomerName}
                      onChange={(e) => setOrderCustomerName(e.target.value)}
                    />
                  </div>
                )}

                {/* Items Builder */}
                <div className="modal-items-box">
                  <div className="items-box-title">
                    <span>Order Line Items</span>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: "4px 8px", fontSize: 11 }}
                      onClick={handleAddOrderItem}
                    >
                      <Plus size={12} /> Add Item
                    </button>
                  </div>

                  {orderItems.map((itm, i) => (
                    <div key={i} className="line-item-row">
                      <select
                        className="form-select"
                        required
                        value={itm.product_id}
                        onChange={(e) =>
                          handleOrderItemChange(i, "product_id", e.target.value)
                        }
                      >
                        <option value="">-- Choose Product --</option>
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} (${p.unit_price}) [Stock: {p.stock_quantity}]
                          </option>
                        ))}
                      </select>
                      <input
                        className="form-input"
                        type="number"
                        min="1"
                        placeholder="Qty"
                        value={itm.quantity}
                        onChange={(e) =>
                          handleOrderItemChange(i, "quantity", e.target.value)
                        }
                      />
                      <input
                        className="form-input"
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder="Price"
                        value={itm.unit_price}
                        onChange={(e) =>
                          handleOrderItemChange(i, "unit_price", e.target.value)
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
                        onClick={() => handleRemoveOrderItem(i)}
                        disabled={orderItems.length === 1}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>

                <div className="modal-summary-box">
                  <div className="summary-row grand-total">
                    <span>Order Total:</span>
                    <span>${calculatedOrderTotal.toFixed(2)}</span>
                  </div>
                </div>

                <div className="form-group">
                  <label>Order Notes / Delivery Details</label>
                  <input
                    className="form-input"
                    type="text"
                    placeholder="Shipping instructions, PO number, etc."
                    value={orderNotes}
                    onChange={(e) => setOrderNotes(e.target.value)}
                  />
                </div>
              </div>

              <div className="inventory-modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowOrderModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-emerald">
                  Create Sales Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── ORDER DETAIL MODAL ── */}
      {selectedOrderDetail && (
        <div className="inventory-modal-overlay">
          <div className="inventory-modal">
            <div className="inventory-modal-header">
              <h2>Order: {selectedOrderDetail.order_number}</h2>
              <button
                className="inventory-modal-close"
                onClick={() => setSelectedOrderDetail(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="inventory-modal-body">
              <div className="detail-meta-grid">
                <div>
                  <div className="detail-label">Customer</div>
                  <div className="detail-val">
                    {selectedOrderDetail.customer?.name || "Direct Customer"}
                  </div>
                </div>
                <div>
                  <div className="detail-label">Status</div>
                  <div style={{ marginTop: 4 }}>
                    <span
                      className={`status-pill status-${selectedOrderDetail.status}`}
                    >
                      ● {selectedOrderDetail.status}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="detail-label">Created At</div>
                  <div className="detail-val">
                    {selectedOrderDetail.created_at?.slice(0, 10)}
                  </div>
                </div>
                <div>
                  <div className="detail-label">Total Amount</div>
                  <div className="detail-val" style={{ color: "#10b981", fontSize: 16 }}>
                    ${(selectedOrderDetail.total_amount ?? 0).toFixed(2)}
                  </div>
                </div>
              </div>

              <div className="modal-items-box">
                <div className="items-box-title">
                  <span>Ordered Items</span>
                </div>
                <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ color: "#94a3b8", textAlign: "left", borderBottom: "1px solid #1e293b" }}>
                      <th style={{ padding: "6px 0" }}>Product</th>
                      <th style={{ padding: "6px 0", textAlign: "center" }}>Qty</th>
                      <th style={{ padding: "6px 0", textAlign: "right" }}>Unit Price</th>
                      <th style={{ padding: "6px 0", textAlign: "right" }}>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(selectedOrderDetail.items || []).map((itm) => (
                      <tr key={itm.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "8px 0", color: "#f1f5f9" }}>
                          {itm.product_name} <span style={{ fontSize: 11, color: "#64748b" }}>({itm.product_sku})</span>
                        </td>
                        <td style={{ padding: "8px 0", textAlign: "center" }}>{itm.quantity}</td>
                        <td style={{ padding: "8px 0", textAlign: "right" }}>${(itm.unit_price ?? 0).toFixed(2)}</td>
                        <td style={{ padding: "8px 0", textAlign: "right", fontWeight: 700, color: "#ffffff" }}>
                          ${(itm.total_amount ?? 0).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {selectedOrderDetail.notes && (
                <div style={{ fontSize: 12, color: "#94a3b8" }}>
                  <strong style={{ color: "#ffffff" }}>Notes: </strong>
                  {selectedOrderDetail.notes}
                </div>
              )}
            </div>

            <div className="inventory-modal-footer">
              {selectedOrderDetail.status !== "fulfilled" && (
                <button
                  type="button"
                  className="btn-emerald"
                  onClick={() => handleFulfillOrder(selectedOrderDetail.id)}
                >
                  <CheckCircle size={14} /> Fulfill Order (Decrements Stock)
                </button>
              )}
              <button
                type="button"
                className="btn-secondary"
                onClick={() => handleConvertToInvoice(selectedOrderDetail.id)}
              >
                <FileText size={14} color="#10b981" /> Convert to Invoice
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setSelectedOrderDetail(null)}
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
