from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import aio_pika
import json

from core.database import get_db
from api.v1.schemas import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    TaskStatusResponse,
    TaskStatus,
    TaskPriority
)
from services.task_service import TaskService
from core.config import settings

router = APIRouter()


async def get_rabbitmq_channel():
    """Получение подключения к RabbitMQ"""
    connection = await aio_pika.connect_robust(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        login=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )
    channel = await connection.channel()
    return channel


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Создание новой задачи"""
    task_service = TaskService(db)
    task = await task_service.create_task(task_data)
    
    # Отправляем задачу в очередь для обработки
    background_tasks.add_task(send_task_to_queue, task.id)
    
    return task


async def send_task_to_queue(task_id: int):
    """Отправка задачи в очередь RabbitMQ"""
    try:
        connection = await aio_pika.connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        )
        
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(settings.RABBITMQ_QUEUE, durable=True)
            
            message_body = json.dumps({"task_id": task_id})
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=queue.name
            )
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        print(f"Error sending task to queue: {str(e)}")


@router.get("/tasks", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    db: AsyncSession = Depends(get_db),
):
    """Получение списка задач с пагинацией и фильтрацией"""
    task_service = TaskService(db)
    skip = (page - 1) * size
    
    tasks, total = await task_service.get_tasks(
        skip=skip,
        limit=size,
        status=status,
        priority=priority
    )
    
    pages = (total + size - 1) // size
    
    return TaskListResponse(
        tasks=tasks,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Получение информации о задаче"""
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Получение статуса задачи"""
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    )


@router.delete("/tasks/{task_id}", status_code=204)
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Отмена задачи"""
    task_service = TaskService(db)
    task = await task_service.cancel_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
    
    return None
