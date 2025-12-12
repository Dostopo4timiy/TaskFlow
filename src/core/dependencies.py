from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from services.task_service import TaskService

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Получение текущего пользователя (заглушка для аутентификации)"""
    # В реальном проекте здесь была бы проверка токена
    if not credentials:
        return None  # Разрешаем анонимный доступ для тестового задания
    
    # Для демо просто возвращаем mock пользователя
    return {"id": 1, "username": "test_user"}


async def get_task_service(
    db: AsyncSession = Depends(get_db)
) -> TaskService:
    """Зависимость для сервиса задач"""
    return TaskService(db)


async def verify_task_exists(
    task_id: int,
    task_service: TaskService = Depends(get_task_service)
):
    """Проверка существования задачи"""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task
