from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from db.models import Task, User, Lead, Customer, Ticket, Order


# ==============================================================================
# USER MANAGEMENT HELPERS
# ==============================================================================

def get_or_create_default_user(db: Session, tenant_id: str) -> User:
    """
    Ensure at least one user exists for assigning tasks in the tenant.
    """
    user = db.query(User).filter(User.tenant_id == tenant_id).first()
    if not user:
        user = User(
            tenant_id=tenant_id,
            email=f"admin@{tenant_id[:8]}.local",
            full_name="Team Lead",
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_tenant_users(db: Session, tenant_id: str) -> List[Dict[str, Any]]:
    """
    Get all active team members for task assignment strictly scoped by tenant_id.
    """
    get_or_create_default_user(db, tenant_id)
    users = db.query(User).filter(User.tenant_id == tenant_id, User.is_active == True).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
        }
        for u in users
    ]


# ==============================================================================
# TASK CRUD OPERATIONS
# ==============================================================================

def create_task(
    db: Session,
    tenant_id: str,
    title: str,
    description: Optional[str] = None,
    status: str = "todo",
    priority: str = "medium",
    due_date: Optional[datetime] = None,
    assigned_to_user_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    ticket_id: Optional[str] = None,
    order_id: Optional[str] = None,
) -> Task:
    """
    Create a new team task strictly scoped to tenant_id.
    Enforces multi-tenant foreign entity validation.
    """
    valid_statuses = {"todo", "in_progress", "review", "done"}
    valid_priorities = {"low", "medium", "high", "urgent"}

    normalized_status = status.lower().strip()
    if normalized_status not in valid_statuses:
        normalized_status = "todo"

    normalized_priority = priority.lower().strip()
    if normalized_priority not in valid_priorities:
        normalized_priority = "medium"

    # Validate assignee belongs to tenant
    if assigned_to_user_id:
        u_exists = db.query(User.id).filter(
            User.tenant_id == tenant_id,
            User.id == assigned_to_user_id
        ).first()
        if not u_exists:
            raise ValueError(f"Assigned user {assigned_to_user_id} not found in this tenant.")

    # Validate linkages
    if lead_id:
        l_exists = db.query(Lead.id).filter(Lead.tenant_id == tenant_id, Lead.id == lead_id).first()
        if not l_exists:
            raise ValueError(f"Lead {lead_id} not found in this tenant.")

    if customer_id:
        c_exists = db.query(Customer.id).filter(Customer.tenant_id == tenant_id, Customer.id == customer_id).first()
        if not c_exists:
            raise ValueError(f"Customer {customer_id} not found in this tenant.")

    if ticket_id:
        t_exists = db.query(Ticket.id).filter(Ticket.tenant_id == tenant_id, Ticket.id == ticket_id).first()
        if not t_exists:
            raise ValueError(f"Ticket {ticket_id} not found in this tenant.")

    if order_id:
        o_exists = db.query(Order.id).filter(Order.tenant_id == tenant_id, Order.id == order_id).first()
        if not o_exists:
            raise ValueError(f"Order {order_id} not found in this tenant.")

    task = Task(
        tenant_id=tenant_id,
        title=title.strip(),
        description=description,
        status=normalized_status,
        priority=normalized_priority,
        due_date=due_date,
        assigned_to_user_id=assigned_to_user_id,
        lead_id=lead_id,
        customer_id=customer_id,
        ticket_id=ticket_id,
        order_id=order_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def _format_task_dict(task: Task) -> Dict[str, Any]:
    """
    Format task into an enriched JSON-ready dictionary with linked entities.
    """
    assignee = task.assigned_to
    # Safe datetime comparison for both PostgreSQL (offset-aware) and SQLite (offset-naive)
    is_overdue = False
    if task.due_date and task.status != "done":
        if task.due_date.tzinfo is not None:
            is_overdue = task.due_date < datetime.now(timezone.utc)
        else:
            is_overdue = task.due_date < datetime.now(timezone.utc).replace(tzinfo=None)

    # Linked entity metadata
    linked_entity = None
    if task.lead:
        linked_entity = {
            "type": "lead",
            "id": task.lead.id,
            "label": f"Lead: {task.lead.title or task.lead.company_name or 'Lead'}",
        }
    elif task.customer:
        linked_entity = {
            "type": "customer",
            "id": task.customer.id,
            "label": f"Customer: {task.customer.name}",
        }
    elif task.ticket:
        linked_entity = {
            "type": "ticket",
            "id": task.ticket.id,
            "label": f"Ticket #{task.ticket.ticket_number}: {task.ticket.issue[:40]}",
        }
    elif task.order:
        linked_entity = {
            "type": "order",
            "id": task.order.id,
            "label": f"Order #{task.order.order_number}",
        }

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "is_overdue": is_overdue,
        "assigned_to": {
            "id": assignee.id,
            "name": assignee.full_name,
            "email": assignee.email,
        } if assignee else None,
        "linked_entity": linked_entity,
        "lead_id": task.lead_id,
        "customer_id": task.customer_id,
        "ticket_id": task.ticket_id,
        "order_id": task.order_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def get_tasks(
    db: Session,
    tenant_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    assigned_to_user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List tasks strictly scoped by tenant_id. Zero cross-tenant leakage.
    """
    query = db.query(Task).filter(Task.tenant_id == tenant_id)

    if status and status.lower() != "all":
        query = query.filter(Task.status == status.lower())

    if priority and priority.lower() != "all":
        query = query.filter(Task.priority == priority.lower())

    if assigned_to_user_id:
        query = query.filter(Task.assigned_to_user_id == assigned_to_user_id)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term),
            )
        )

    total_count = query.count()
    tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()

    return [_format_task_dict(t) for t in tasks], total_count


def get_task_by_id(db: Session, tenant_id: str, task_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single task strictly isolated to tenant_id.
    """
    task = db.query(Task).filter(
        Task.tenant_id == tenant_id,
        Task.id == task_id
    ).first()

    if not task:
        return None

    return _format_task_dict(task)


def update_task(
    db: Session,
    tenant_id: str,
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[datetime] = None,
    assigned_to_user_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    ticket_id: Optional[str] = None,
    order_id: Optional[str] = None,
) -> Optional[Task]:
    """
    Update task fields strictly scoped to tenant_id.
    """
    task = db.query(Task).filter(
        Task.tenant_id == tenant_id,
        Task.id == task_id
    ).first()

    if not task:
        return None

    if title is not None:
        task.title = title.strip()
    if description is not None:
        task.description = description
    if status is not None:
        valid_statuses = {"todo", "in_progress", "review", "done"}
        if status.lower() in valid_statuses:
            task.status = status.lower()
    if priority is not None:
        valid_priorities = {"low", "medium", "high", "urgent"}
        if priority.lower() in valid_priorities:
            task.priority = priority.lower()
    if due_date is not None:
        task.due_date = due_date
    if assigned_to_user_id is not None:
        if assigned_to_user_id == "":
            task.assigned_to_user_id = None
        else:
            task.assigned_to_user_id = assigned_to_user_id
    if lead_id is not None:
        task.lead_id = lead_id or None
    if customer_id is not None:
        task.customer_id = customer_id or None
    if ticket_id is not None:
        task.ticket_id = ticket_id or None
    if order_id is not None:
        task.order_id = order_id or None

    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, tenant_id: str, task_id: str, status: str) -> Optional[Task]:
    """
    Quick status transition for Kanban drag-and-drop or single-click update.
    """
    valid_statuses = {"todo", "in_progress", "review", "done"}
    new_status = status.lower().strip()
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")

    task = db.query(Task).filter(
        Task.tenant_id == tenant_id,
        Task.id == task_id
    ).first()

    if not task:
        return None

    task.status = new_status
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, tenant_id: str, task_id: str) -> bool:
    """
    Delete task strictly scoped to tenant_id.
    """
    task = db.query(Task).filter(
        Task.tenant_id == tenant_id,
        Task.id == task_id
    ).first()

    if not task:
        return False

    db.delete(task)
    db.commit()
    return True


def get_task_kanban(db: Session, tenant_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group tasks into 4 Kanban stages: todo, in_progress, review, done.
    """
    tasks = db.query(Task).filter(Task.tenant_id == tenant_id).order_by(Task.created_at.desc()).all()

    board = {
        "todo": [],
        "in_progress": [],
        "review": [],
        "done": []
    }

    for t in tasks:
        formatted = _format_task_dict(t)
        st = t.status if t.status in board else "todo"
        board[st].append(formatted)

    return board


def get_task_stats(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Compute task metrics strictly scoped by tenant_id.
    """
    tasks = db.query(Task).filter(Task.tenant_id == tenant_id).all()

    total = len(tasks)
    todo = sum(1 for t in tasks if t.status == "todo")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    review = sum(1 for t in tasks if t.status == "review")
    done = sum(1 for t in tasks if t.status == "done")

    now_utc = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)
    overdue = sum(
        1 for t in tasks
        if t.due_date and t.status != "done" and (
            (t.due_date < now_utc) if t.due_date.tzinfo is not None else (t.due_date < now_naive)
        )
    )
    urgent = sum(1 for t in tasks if t.priority in ("urgent", "high") and t.status != "done")

    completion_rate = round((done / total * 100.0), 1) if total > 0 else 0.0

    return {
        "total": total,
        "todo": todo,
        "in_progress": in_progress,
        "review": review,
        "done": done,
        "overdue": overdue,
        "urgent": urgent,
        "completion_rate": completion_rate,
    }
