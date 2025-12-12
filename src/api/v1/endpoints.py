from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.api.dependencies import get_db
from src.api.v1.schemas import (
    TaskCreate, TaskResponse, TaskListResponse, TaskStatus
)
from src.models.task import Task as TaskModel
from src.services.task_service import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание новой задачи"""
    task_service = TaskService(db)
    task = await task_service.create_task(task_data)
    return task


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка задач с фильтрацией и пагинацией"""
    task_service = TaskService(db)
    tasks, total = await task_service.get_tasks(
        status=status,
        priority=priority,
        page=page,
        size=size
    )
    return TaskListResponse(
        tasks=tasks,
        total=total,
        page=page,
        size=size
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о конкретной задаче"""
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Отмена задачи"""
    task_service = TaskService(db)
    success = await task_service.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
    return None


@router.get("/{task_id}/status")
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получение статуса задачи"""
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": task.status}
