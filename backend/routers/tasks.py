from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.session import get_db
from core.tenancy import get_current_tenant_id
from services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Task title")
    description: Optional[str] = Field(None, description="Detailed task description")
    status: Optional[str] = Field("todo", description="todo, in_progress, review, done")
    priority: Optional[str] = Field("medium", description="low, medium, high, urgent")
    due_date: Optional[datetime] = Field(None, description="Due date timestamp")
    assigned_to_user_id: Optional[str] = Field(None, description="Assigned team member ID")
    lead_id: Optional[str] = Field(None, description="Linked Lead ID")
    customer_id: Optional[str] = Field(None, description="Linked Customer ID")
    ticket_id: Optional[str] = Field(None, description="Linked Support Ticket ID")
    order_id: Optional[str] = Field(None, description="Linked Inventory Order ID")


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to_user_id: Optional[str] = None
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    ticket_id: Optional[str] = None
    order_id: Optional[str] = None


class TaskStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Target status: todo, in_progress, review, done")


# ==============================================================================
# TASK ENDPOINTS
# ==============================================================================

@router.get("")
def list_tasks(
    status: Optional[str] = Query(None, description="Filter: todo, in_progress, review, done, or all"),
    priority: Optional[str] = Query(None, description="Filter: low, medium, high, urgent, or all"),
    search: Optional[str] = Query(None, description="Search in title or description"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    List tasks strictly filtered by tenant_id. Zero cross-tenant leakage.
    """
    tasks, total = task_service.get_tasks(
        db=db,
        tenant_id=tenant_id,
        status=status,
        priority=priority,
        search=search,
        assigned_to_user_id=assigned_to,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "tasks": tasks,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task_endpoint(
    req: TaskCreateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Create a new task strictly scoped to authenticated tenant.
    """
    try:
        task = task_service.create_task(
            db=db,
            tenant_id=tenant_id,
            title=req.title,
            description=req.description,
            status=req.status or "todo",
            priority=req.priority or "medium",
            due_date=req.due_date,
            assigned_to_user_id=req.assigned_to_user_id,
            lead_id=req.lead_id,
            customer_id=req.customer_id,
            ticket_id=req.ticket_id,
            order_id=req.order_id,
        )
        return task_service.get_task_by_id(db, tenant_id=tenant_id, task_id=task.id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/kanban")
def get_kanban_board(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get grouped Kanban board representation (todo, in_progress, review, done).
    """
    return task_service.get_task_kanban(db, tenant_id=tenant_id)


@router.get("/stats")
def task_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Task analytics, overdue counts, and completion rates for authenticated tenant.
    """
    return task_service.get_task_stats(db, tenant_id=tenant_id)


@router.get("/users")
def get_team_members(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    List available team members for task assignment.
    """
    return task_service.get_tenant_users(db, tenant_id=tenant_id)


@router.get("/{task_id}")
def get_task_endpoint(
    task_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Get single task detail with assignee and linked entity details.
    """
    task = task_service.get_task_by_id(db, tenant_id=tenant_id, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized.")
    return task


@router.patch("/{task_id}")
def update_task_endpoint(
    task_id: str,
    req: TaskUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Update task attributes strictly scoped to tenant_id.
    """
    try:
        task = task_service.update_task(
            db=db,
            tenant_id=tenant_id,
            task_id=task_id,
            title=req.title,
            description=req.description,
            status=req.status,
            priority=req.priority,
            due_date=req.due_date,
            assigned_to_user_id=req.assigned_to_user_id,
            lead_id=req.lead_id,
            customer_id=req.customer_id,
            ticket_id=req.ticket_id,
            order_id=req.order_id,
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found or unauthorized.")
        return task_service.get_task_by_id(db, tenant_id=tenant_id, task_id=task.id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.patch("/{task_id}/status")
def update_task_status_endpoint(
    task_id: str,
    req: TaskStatusUpdateRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Quick status transition (Kanban drag-and-drop or single click).
    """
    try:
        task = task_service.update_task_status(
            db=db,
            tenant_id=tenant_id,
            task_id=task_id,
            status=req.status,
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found or unauthorized.")
        return task_service.get_task_by_id(db, tenant_id=tenant_id, task_id=task.id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.delete("/{task_id}")
def delete_task_endpoint(
    task_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """
    Delete task strictly scoped to tenant_id.
    """
    success = task_service.delete_task(db, tenant_id=tenant_id, task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized.")
    return {"message": "Task deleted successfully."}
