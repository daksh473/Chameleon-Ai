import { useState, useEffect, useRef } from "react";
import { Building2, ChevronDown, Check, Plus, X } from "lucide-react";
import "./TenantSwitcher.css";

const API = "http://localhost:8000";

// Global fetch interceptor for multi-tenancy
if (typeof window !== "undefined" && !window.__bms_fetch_intercepted) {
  window.__bms_fetch_intercepted = true;
  const originalFetch = window.fetch;
  window.fetch = function (url, options = {}) {
    const tenantId = localStorage.getItem("bms_tenant_id");
    if (tenantId && typeof url === "string" && (url.includes("8000") || url.startsWith("/"))) {
      options.headers = {
        ...(options.headers || {}),
        "X-Tenant-ID": tenantId,
      };
    }
    return originalFetch(url, options);
  };
}

export default function TenantSwitcher() {
  const [tenants, setTenants] = useState([]);
  const [currentTenant, setCurrentTenant] = useState(null);
  const [open, setOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const dropdownRef = useRef(null);

  const fetchTenants = async () => {
    try {
      const res = await fetch(`${API}/tenants`);
      if (res.ok) {
        const list = await res.json();
        setTenants(list);

        const savedId = localStorage.getItem("bms_tenant_id");
        const active = list.find((t) => t.id === savedId) || list[0];
        if (active) {
          setCurrentTenant(active);
          localStorage.setItem("bms_tenant_id", active.id);
        }
      }
    } catch (err) {
      console.error("Error loading tenants:", err);
    }
  };

  useEffect(() => {
    fetchTenants();

    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectTenant = (tenant) => {
    if (currentTenant?.id === tenant.id) {
      setOpen(false);
      return;
    }
    setCurrentTenant(tenant);
    localStorage.setItem("bms_tenant_id", tenant.id);
    setOpen(false);
    // Reload to refresh all active module workspaces with new tenant context
    window.location.reload();
  };

  const handleCreateTenant = async (e) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;

    try {
      const res = await fetch(`${API}/tenants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newOrgName.trim() }),
      });
      if (res.ok) {
        const created = await res.json();
        setShowCreateModal(false);
        setNewOrgName("");
        handleSelectTenant(created);
      } else {
        alert("Failed to create organization.");
      }
    } catch (err) {
      alert("Error creating organization.");
    }
  };

  return (
    <div className="tenant-switcher-container" ref={dropdownRef}>
      <button className="tenant-current-btn" onClick={() => setOpen(!open)}>
        <Building2 size={15} color="#10b981" />
        <span>{currentTenant?.name || "Loading Org..."}</span>
        <span className="tenant-tag">ORG</span>
        <ChevronDown size={13} color="#94a3b8" />
      </button>

      {open && (
        <div className="tenant-dropdown-menu">
          <div className="tenant-menu-header">Switch Organization</div>
          {tenants.map((t) => (
            <button
              key={t.id}
              className={`tenant-item-btn ${
                currentTenant?.id === t.id ? "active" : ""
              }`}
              onClick={() => handleSelectTenant(t)}
            >
              <span>{t.name}</span>
              {currentTenant?.id === t.id && <Check size={14} color="#10b981" />}
            </button>
          ))}

          <div className="tenant-divider" />

          <button
            className="tenant-create-btn"
            onClick={() => {
              setOpen(false);
              setShowCreateModal(true);
            }}
          >
            <Plus size={14} /> Provision New Org
          </button>
        </div>
      )}

      {/* Create Org Modal */}
      {showCreateModal && (
        <div className="inventory-modal-overlay">
          <div className="inventory-modal" style={{ maxWidth: 420 }}>
            <div className="inventory-modal-header">
              <h2>Provision New Organization</h2>
              <button
                className="inventory-modal-close"
                onClick={() => setShowCreateModal(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateTenant}>
              <div className="inventory-modal-body">
                <div className="form-group">
                  <label>Organization Name *</label>
                  <input
                    className="form-input"
                    type="text"
                    required
                    placeholder="e.g. Acme Global Enterprises"
                    value={newOrgName}
                    onChange={(e) => setNewOrgName(e.target.value)}
                  />
                </div>
                <p style={{ fontSize: 12, color: "#94a3b8", margin: 0 }}>
                  Each organization receives a 100% isolated BMS workspace with independent CRM, Billing, Inventory, Tasks, and Support channels.
                </p>
              </div>

              <div className="inventory-modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-emerald">
                  Provision Organization
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
