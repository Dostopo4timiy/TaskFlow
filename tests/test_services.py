import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.services.task_service import TaskService
from src.models.task import Task, TaskStatus, TaskPriority
from src.api.v1.schemas import TaskCreate, TaskUpdate


@pytest.mark.asyncio
async def test_create_task(db_session):
    """Тест создания задачи"""
    task_service = TaskService(db_session)
    
    task_data = TaskCreate(
        title="Test Task",
        description="Test Description",
        priority="high"
    )
    
    task = await task_service.create_task(task_data)
    
    assert task.id is not None
    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.NEW


@pytest.mark.asyncio
async def test_get_task(db_session):
    """Тест получения задачи по ID"""
    task_service = TaskService(db_session)
    
    # Создаем задачу
    task_data = TaskCreate(
        title="Test Task",
        description="Test Description",
        priority="medium"
    )
    created_task = await task_service.create_task(task_data)
    
    # Получаем задачу
    retrieved_task = await task_service.get_task(created_task.id)
    
    assert retrieved_task is not None
    assert retrieved_task.id == created_task.id
    assert retrieved_task.title == "Test Task"


@pytest.mark.asyncio
async def test_get_nonexistent_task(db_session):
    """Тест получения несуществующей задачи"""
    task_service = TaskService(db_session)
    task = await task_service.get_task(999)
    assert task is None


@pytest.mark.asyncio
async def test_get_tasks_with_filters(db_session):
    """Тест получения задач с фильтрацией"""
    task_service = TaskService(db_session)
    
    # Создаем несколько задач
    for i in range(5):
        task_data = TaskCreate(
            title=f"Task {i}",
            description=f"Description {i}",
            priority="medium" if i % 2 == 0 else "high"
        )
        await task_service.create_task(task_data)
    
    # Получаем задачи с фильтрацией по приоритету
    tasks, total = await task_service.get_tasks(
        skip=0,
        limit=10,
        priority=TaskPriority.HIGH
    )
    
    assert len(tasks) > 0
    assert all(task.priority == TaskPriority.HIGH for task in tasks)
    assert total > 0


@pytest.mark.asyncio
async def test_update_task(db_session):
    """Тест обновления задачи"""
    task_service = TaskService(db_session)
    
    # Создаем задачу
    task_data = TaskCreate(
        title="Original Task",
        description="Original Description",
        priority="low"
    )
    task = await task_service.create_task(task_data)
    
    # Обновляем задачу
    update_data = TaskUpdate(
        status="in_progress",
        result="Task in progress"
    )
    updated_task = await task_service.update_task(task.id, update_data)
    
    assert updated_task is not None
    assert updated_task.status == TaskStatus.IN_PROGRESS
    assert updated_task.started_at is not None
    assert updated_task.result == "Task in progress"


@pytest.mark.asyncio
async def test_cancel_task(db_session):
    """Тест отмены задачи"""
    task_service = TaskService(db_session)
    
    # Создаем задачу
    task_data = TaskCreate(title="Task to Cancel")
    task = await task_service.create_task(task_data)
    
    # Обновляем статус на IN_PROGRESS
    await task_service.update_task(task.id, TaskUpdate(status="in_progress"))
    
    # Отменяем задачу
    cancelled_task = await task_service.cancel_task(task.id)
    
    assert cancelled_task is not None
    assert cancelled_task.status == TaskStatus.CANCELLED
    assert cancelled_task.error_info == "Task cancelled by user"
    assert cancelled_task.completed_at is not None


@pytest.mark.asyncio
async def test_delete_task(db_session):
    """Тест удаления задачи"""
    task_service = TaskService(db_session)
    
    # Создаем задачу
    task_data = TaskCreate(title="Task to Delete")
    task = await task_service.create_task(task_data)
    
    # Удаляем задачу
    result = await task_service.delete_task(task.id)
    assert result is True
    
    # Проверяем, что задача удалена
    deleted_task = await task_service.get_task(task.id)
    assert deleted_task is None


@pytest.mark.asyncio
async def test_worker_process_task():
    """Тест обработки задачи воркером"""
    from src.services.worker import TaskWorker
    
    # Мокаем зависимости
    with patch('src.services.worker.create_async_engine') as mock_engine, \
         patch('src.services.worker.sessionmaker') as mock_sessionmaker, \
         patch('src.services.task_service.TaskService') as mock_service:
        
        # Настраиваем моки
        mock_session = AsyncMock()
        mock_service_instance = AsyncMock()
        mock_service_instance.get_task.return_value = AsyncMock(
            priority=AsyncMock(value="medium")
        )
        mock_service.return_value = mock_service_instance
        
        worker = TaskWorker()
        
        # Вызываем обработку задачи
        await worker.process_task(1)
        
        # Проверяем вызовы
        assert mock_service_instance.update_task.call_count >= 2
