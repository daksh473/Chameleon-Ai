import { useState, useEffect } from "react";
import {
  CheckSquare,
  Clock,
  AlertTriangle,
  CheckCircle,
  Plus,
  RefreshCw,
  Search,
  LayoutGrid,
  List,
  ChevronRight,
  ChevronLeft,
  Trash2,
  Edit2,
  X,
  User,
  Link as LinkIcon,
  Calendar,
} from "lucide-react";
import "./TasksView.css";

const API = "http://localhost:8000";

const STAGES = [
  { id: "todo", label: "To Do", color: "#94a3b8" },
  { id: "in_progress", label: "In Progress", color: "#34d399" },
  { id: "review", label: "In Review", color: "#a855f7" },
  { id: "done", label: "Completed", color: "#10b981" },
];

export default function TasksView() {
  const [viewMode, setViewMode] = useState("kanban"); // 'kanban' | 'list'
  const [stats, setStats] = useState(null);
  const [kanban, setKanban] = useState({ todo: [], in_progress: [], review: [], done: [] });
  const [tasksList, setTasksList] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Modals
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Form State
  const [formTitle, setFormTitle] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formPriority, setFormPriority] = useState("medium");
  const [formStatus, setFormStatus] = useState("todo");
  const [formDueDate, setFormDueDate] = useState("");
  const [formAssigneeId, setFormAssigneeId] = useState("");

  // Polymorphic Linkage Form State
  const [linkageType, setLinkageType] = useState("none"); // none | lead | customer | ticket | order
  const [linkageId, setLinkageId] = useState("");
  const [availableLeads, setAvailableLeads] = useState([]);
  const [availableCustomers, setAvailableCustomers] = useState([]);
  const [availableTickets, setAvailableTickets] = useState([]);
  const [availableOrders, setAvailableOrders] = useState([]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [stRes, kbRes, lsRes, usRes] = await Promise.all([
        fetch(`${API}/tasks/stats`).then((r) => (r.ok ? r.json() : null)),
        fetch(`${API}/tasks/kanban`).then((r) =>
          r.ok ? r.json() : { todo: [], in_progress: [], review: [], done: [] }
        ),
        fetch(`${API}/tasks?search=${encodeURIComponent(searchQuery)}`).then(
          (r) => (r.ok ? r.json() : { tasks: [] })
        ),
        fetch(`${API}/tasks/users`).then((r) => (r.ok ? r.json() : [])),
      ]);

      setStats(stRes);
      setKanban(kbRes || { todo: [], in_progress: [], review: [], done: [] });
      setTasksList(lsRes.tasks || []);
      setUsers(Array.isArray(usRes) ? usRes : []);
    } catch (err) {
      console.error("Task fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Fetch linkage options when modal opens or linkage type changes
  const fetchLinkageData = async (type) => {
    try {
      if (type === "lead") {
        const res = await fetch(`${API}/crm/deals`);
        if (res.ok) setAvailableLeads(await res.json());
      } else if (type === "customer") {
        const res = await fetch(`${API}/crm/customers`);
        if (res.ok) setAvailableCustomers(await res.json());
      } else if (type === "ticket") {
        const res = await fetch(`${API}/tickets`);
        if (res.ok) setAvailableTickets(await res.json());
      } else if (type === "order") {
        const res = await fetch(`${API}/inventory/orders`);
        if (res.ok) {
          const d = await res.json();
          setAvailableOrders(d.orders || []);
        }
      }
    } catch (e) {
      console.error("Linkage fetch error:", e);
    }
  };

  const handleLinkageTypeChange = (type) => {
    setLinkageType(type);
    setLinkageId("");
    if (type !== "none") {
      fetchLinkageData(type);
    }
  };

  // Open Create Modal
  const handleOpenCreateModal = (defaultStatus = "todo") => {
    setEditingTask(null);
    setFormTitle("");
    setFormDesc("");
    setFormPriority("medium");
    setFormStatus(defaultStatus);
    setFormDueDate("");
    setFormAssigneeId(users[0]?.id || "");
    setLinkageType("none");
    setLinkageId("");
    setShowTaskModal(true);
  };

  // Open Edit Modal
  const handleOpenEditModal = (task) => {
    setEditingTask(task);
    setFormTitle(task.title);
    setFormDesc(task.description || "");
    setFormPriority(task.priority || "medium");
    setFormStatus(task.status || "todo");
    setFormDueDate(task.due_date ? task.due_date.slice(0, 16) : "");
    setFormAssigneeId(task.assigned_to?.id || "");

    if (task.lead_id) {
      setLinkageType("lead");
      setLinkageId(task.lead_id);
      fetchLinkageData("lead");
    } else if (task.customer_id) {
      setLinkageType("customer");
      setLinkageId(task.customer_id);
      fetchLinkageData("customer");
    } else if (task.ticket_id) {
      setLinkageType("ticket");
      setLinkageId(task.ticket_id);
      fetchLinkageData("ticket");
    } else if (task.order_id) {
      setLinkageType("order");
      setLinkageId(task.order_id);
      fetchLinkageData("order");
    } else {
      setLinkageType("none");
      setLinkageId("");
    }

    setShowTaskModal(true);
  };

  // Save Task (Create or Update)
  const handleSaveTask = async (e) => {
    e.preventDefault();
    if (!formTitle.trim()) return;

    const payload = {
      title: formTitle,
      description: formDesc || null,
      priority: formPriority,
      status: formStatus,
      due_date: formDueDate ? new Date(formDueDate).toISOString() : null,
      assigned_to_user_id: formAssigneeId || null,
      lead_id: linkageType === "lead" ? linkageId : null,
      customer_id: linkageType === "customer" ? linkageId : null,
      ticket_id: linkageType === "ticket" ? linkageId : null,
      order_id: linkageType === "order" ? linkageId : null,
    };

    try {
      if (editingTask) {
        const res = await fetch(`${API}/tasks/${editingTask.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          showToast("Task updated successfully.");
          setShowTaskModal(false);
          fetchData();
        }
      } else {
        const res = await fetch(`${API}/tasks`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          showToast("Task created successfully!");
          setShowTaskModal(false);
          fetchData();
        }
      }
    } catch (err) {
      alert("Error saving task.");
    }
  };

  // Quick Move Column
  const handleMoveStatus = async (taskId, targetStatus) => {
    try {
      const res = await fetch(`${API}/tasks/${taskId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: targetStatus }),
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      showToast("Failed to move task.");
    }
  };

  // Delete Task
  const handleDeleteTask = async (taskId) => {
    if (!window.confirm("Are you sure you want to delete this task?")) return;
    try {
      const res = await fetch(`${API}/tasks/${taskId}`, { method: "DELETE" });
      if (res.ok) {
        showToast("Task deleted.");
        fetchData();
      }
    } catch (err) {
      showToast("Error deleting task.");
    }
  };

  return (
    <div className="tasks-container">
      {/* ── Header ── */}
      <div className="tasks-header">
        <div className="tasks-title-group">
          <h1>
            <CheckSquare size={24} color="#10b981" />
            Tasks & Collaboration
          </h1>
          <p>
            Assign team tasks, track execution across Kanban stages, monitor deadlines, and link work to Leads, Customers, Tickets, and Orders.
          </p>
        </div>

        <div className="tasks-actions">
          {/* View Switcher */}
          <div className="tasks-view-switch">
            <button
              className={`tasks-switch-btn ${viewMode === "kanban" ? "active" : ""}`}
              onClick={() => setViewMode("kanban")}
            >
              <LayoutGrid size={13} /> Kanban
            </button>
            <button
              className={`tasks-switch-btn ${viewMode === "list" ? "active" : ""}`}
              onClick={() => setViewMode("list")}
            >
              <List size={13} /> List
            </button>
          </div>

          <button className="btn-secondary" onClick={fetchData} title="Refresh data">
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            Refresh
          </button>
          <button className="btn-emerald" onClick={() => handleOpenCreateModal("todo")}>
            <Plus size={16} />
            Create Task
          </button>
        </div>
      </div>

      {/* ── KPI Cards ── */}
      <div className="tasks-kpi-grid">
        <div className="tasks-kpi-card">
          <div className="tasks-kpi-icon-wrap kpi-icon-green">
            <CheckSquare size={20} />
          </div>
          <div className="tasks-kpi-info">
            <span className="tasks-kpi-label">Total Tasks</span>
            <span className="tasks-kpi-value emerald">
              {stats?.total ?? 0}
            </span>
          </div>
        </div>

        <div className="tasks-kpi-card">
          <div className="tasks-kpi-icon-wrap kpi-icon-amber">
            <Clock size={20} />
          </div>
          <div className="tasks-kpi-info">
            <span className="tasks-kpi-label">In Progress</span>
            <span className="tasks-kpi-value">
              {stats?.in_progress ?? 0}
            </span>
          </div>
        </div>

        <div className="tasks-kpi-card">
          <div className="tasks-kpi-icon-wrap kpi-icon-red">
            <AlertTriangle size={20} />
          </div>
          <div className="tasks-kpi-info">
            <span className="tasks-kpi-label">Overdue</span>
            <span className="tasks-kpi-value" style={{ color: "#ef4444" }}>
              {stats?.overdue ?? 0}
            </span>
          </div>
        </div>

        <div className="tasks-kpi-card">
          <div className="tasks-kpi-icon-wrap kpi-icon-emerald">
            <CheckCircle size={20} />
          </div>
          <div className="tasks-kpi-info">
            <span className="tasks-kpi-label">Completed</span>
            <span className="tasks-kpi-value">
              {stats?.done ?? 0} ({stats?.completion_rate ?? 0}%)
            </span>
          </div>
        </div>
      </div>

      {/* ════════ KANBAN BOARD ════════ */}
      {viewMode === "kanban" && (
        <div className="kanban-board">
          {STAGES.map((col, colIdx) => {
            const items = kanban[col.id] || [];
            return (
              <div key={col.id} className="kanban-column">
                <div className="kanban-col-header">
                  <span className="kanban-col-title" style={{ color: col.color }}>
                    ● {col.label}
                  </span>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span className="col-badge">{items.length}</span>
                    <button
                      className="move-arrow-btn"
                      title={`Add task to ${col.label}`}
                      onClick={() => handleOpenCreateModal(col.id)}
                    >
                      <Plus size={12} />
                    </button>
                  </div>
                </div>

                <div className="kanban-card-list">
                  {items.map((task) => (
                    <div key={task.id} className="task-card">
                      <div className="task-card-header">
                        <span className={`priority-pill priority-${task.priority}`}>
                          {task.priority}
                        </span>
                        <div style={{ display: "flex", gap: 4 }}>
                          <button
                            className="move-arrow-btn"
                            title="Edit"
                            onClick={() => handleOpenEditModal(task)}
                          >
                            <Edit2 size={11} />
                          </button>
                          <button
                            className="move-arrow-btn"
                            title="Delete"
                            onClick={() => handleDeleteTask(task.id)}
                          >
                            <Trash2 size={11} color="#ef4444" />
                          </button>
                        </div>
                      </div>

                      <div className="task-card-title">{task.title}</div>
                      {task.description && (
                        <div className="task-card-desc">
                          {task.description.slice(0, 75)}
                          {task.description.length > 75 ? "..." : ""}
                        </div>
                      )}

                      {task.linked_entity && (
                        <div className="task-linked-chip">
                          <LinkIcon size={11} />
                          <span>{task.linked_entity.label}</span>
                        </div>
                      )}

                      <div className="task-card-footer">
                        <div className="task-assignee">
                          <div className="assignee-avatar">
                            {task.assigned_to?.name?.charAt(0) || "U"}
                          </div>
                          <span>{task.assigned_to?.name || "Unassigned"}</span>
                        </div>

                        {task.due_date && (
                          <div
                            className={`task-due-date ${
                              task.is_overdue ? "overdue" : ""
                            }`}
                          >
                            {task.is_overdue && <AlertTriangle size={11} />}
                            <span>{task.due_date.slice(5, 10)}</span>
                          </div>
                        )}
                      </div>

                      {/* Quick Move Arrows */}
                      <div className="task-card-move-bar">
                        {colIdx > 0 && (
                          <button
                            className="move-arrow-btn"
                            title={`Move to ${STAGES[colIdx - 1].label}`}
                            onClick={() =>
                              handleMoveStatus(task.id, STAGES[colIdx - 1].id)
                            }
                          >
                            <ChevronLeft size={13} />
                          </button>
                        )}
                        {colIdx < STAGES.length - 1 && (
                          <button
                            className="move-arrow-btn"
                            title={`Move to ${STAGES[colIdx + 1].label}`}
                            onClick={() =>
                              handleMoveStatus(task.id, STAGES[colIdx + 1].id)
                            }
                          >
                            <ChevronRight size={13} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}

                  {items.length === 0 && (
                    <div
                      style={{
                        textAlign: "center",
                        padding: "30px 10px",
                        color: "#475569",
                        fontSize: 12,
                      }}
                    >
                      No tasks in this stage
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ════════ LIST TABLE VIEW ════════ */}
      {viewMode === "list" && (
        <div className="inventory-table-card">
          {tasksList.length === 0 ? (
            <div className="billing-empty-state">
              <CheckSquare size={36} color="#10b981" />
              <h3>No Tasks Found</h3>
              <p>Create your first task to start collaborating with your team.</p>
            </div>
          ) : (
            <table className="inventory-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Stage</th>
                  <th>Priority</th>
                  <th>Assignee</th>
                  <th>Linked To</th>
                  <th>Due Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tasksList.map((t) => (
                  <tr key={t.id}>
                    <td>
                      <div style={{ fontWeight: 700, color: "#ffffff" }}>
                        {t.title}
                      </div>
                      {t.description && (
                        <div style={{ fontSize: 11, color: "#64748b" }}>
                          {t.description.slice(0, 50)}
                        </div>
                      )}
                    </td>
                    <td>
                      <span className={`status-pill status-${t.status}`}>
                        ● {t.status}
                      </span>
                    </td>
                    <td>
                      <span className={`priority-pill priority-${t.priority}`}>
                        {t.priority}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <div className="assignee-avatar">
                          {t.assigned_to?.name?.charAt(0) || "U"}
                        </div>
                        <span>{t.assigned_to?.name || "Unassigned"}</span>
                      </div>
                    </td>
                    <td>
                      {t.linked_entity ? (
                        <span className="task-linked-chip">
                          <LinkIcon size={11} /> {t.linked_entity.label}
                        </span>
                      ) : (
                        <span style={{ color: "#64748b" }}>None</span>
                      )}
                    </td>
                    <td>
                      {t.due_date ? (
                        <span style={{ color: t.is_overdue ? "#ef4444" : "#94a3b8" }}>
                          {t.due_date.slice(0, 10)}
                        </span>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td>
                      <div className="row-actions">
                        <button
                          className="icon-action-btn"
                          title="Edit Task"
                          onClick={() => handleOpenEditModal(t)}
                        >
                          <Edit2 size={13} />
                        </button>
                        <button
                          className="icon-action-btn delete"
                          title="Delete Task"
                          onClick={() => handleDeleteTask(t.id)}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── CREATE / EDIT TASK MODAL ── */}
      {showTaskModal && (
        <div className="inventory-modal-overlay">
          <div className="inventory-modal" style={{ maxWidth: 620 }}>
            <div className="inventory-modal-header">
              <h2>{editingTask ? "Edit Task" : "Create Team Task"}</h2>
              <button
                className="inventory-modal-close"
                onClick={() => setShowTaskModal(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveTask}>
              <div className="inventory-modal-body">
                <div className="form-group">
                  <label>Task Title *</label>
                  <input
                    className="form-input"
                    type="text"
                    required
                    placeholder="e.g. Schedule onboarding call with client"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    className="form-textarea"
                    rows={3}
                    placeholder="Details, acceptance criteria, or context..."
                    value={formDesc}
                    onChange={(e) => setFormDesc(e.target.value)}
                  />
                </div>

                <div className="form-group-row">
                  <div className="form-group">
                    <label>Priority</label>
                    <select
                      className="form-select"
                      value={formPriority}
                      onChange={(e) => setFormPriority(e.target.value)}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Stage / Status</label>
                    <select
                      className="form-select"
                      value={formStatus}
                      onChange={(e) => setFormStatus(e.target.value)}
                    >
                      <option value="todo">To Do</option>
                      <option value="in_progress">In Progress</option>
                      <option value="review">In Review</option>
                      <option value="done">Completed</option>
                    </select>
                  </div>
                </div>

                <div className="form-group-row">
                  <div className="form-group">
                    <label>Due Date & Time</label>
                    <input
                      className="form-input"
                      type="datetime-local"
                      value={formDueDate}
                      onChange={(e) => setFormDueDate(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label>Assign Team Member</label>
                    <select
                      className="form-select"
                      value={formAssigneeId}
                      onChange={(e) => setFormAssigneeId(e.target.value)}
                    >
                      <option value="">-- Unassigned --</option>
                      {users.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.full_name} ({u.role})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Polymorphic Linkage */}
                <div className="modal-items-box">
                  <label style={{ fontSize: 12, fontWeight: 700, color: "#10b981" }}>
                    LINK TO BMS ENTITY (OPTIONAL)
                  </label>
                  <div className="task-linkage-row">
                    <select
                      className="form-select"
                      value={linkageType}
                      onChange={(e) => handleLinkageTypeChange(e.target.value)}
                    >
                      <option value="none">None / General</option>
                      <option value="lead">CRM Lead / Deal</option>
                      <option value="customer">CRM Customer</option>
                      <option value="ticket">Support Ticket</option>
                      <option value="order">Inventory Order</option>
                    </select>

                    {linkageType === "lead" && (
                      <select
                        className="form-select"
                        value={linkageId}
                        onChange={(e) => setLinkageId(e.target.value)}
                      >
                        <option value="">-- Choose Lead --</option>
                        {availableLeads.map((l) => (
                          <option key={l.id} value={l.id}>
                            {l.title || l.name} (${l.value || l.estimated_value || 0})
                          </option>
                        ))}
                      </select>
                    )}

                    {linkageType === "customer" && (
                      <select
                        className="form-select"
                        value={linkageId}
                        onChange={(e) => setLinkageId(e.target.value)}
                      >
                        <option value="">-- Choose Customer --</option>
                        {availableCustomers.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name} {c.company ? `(${c.company})` : ""}
                          </option>
                        ))}
                      </select>
                    )}

                    {linkageType === "ticket" && (
                      <select
                        className="form-select"
                        value={linkageId}
                        onChange={(e) => setLinkageId(e.target.value)}
                      >
                        <option value="">-- Choose Ticket --</option>
                        {availableTickets.map((tk) => (
                          <option key={tk.id} value={tk.id}>
                            #{tk.ticket_number || tk.id.slice(0, 6)}: {tk.issue?.slice(0, 30)}
                          </option>
                        ))}
                      </select>
                    )}

                    {linkageType === "order" && (
                      <select
                        className="form-select"
                        value={linkageId}
                        onChange={(e) => setLinkageId(e.target.value)}
                      >
                        <option value="">-- Choose Order --</option>
                        {availableOrders.map((od) => (
                          <option key={od.id} value={od.id}>
                            {od.order_number} (${od.total_amount})
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
              </div>

              <div className="inventory-modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowTaskModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-emerald">
                  {editingTask ? "Save Changes" : "Create Task"}
                </button>
              </div>
            </form>
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
