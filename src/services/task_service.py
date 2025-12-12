from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime
import uuid

from models.task import Task, TaskStatus, TaskPriority
from api.v1.schemas import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_task(self, task_data: TaskCreate) -> Task:
        """Создание новой задачи"""
        task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=TaskPriority(task_data.priority.value),
            status=TaskStatus.NEW
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def get_task(self, task_id: int) -> Optional[Task]:
        """Получение задачи по ID"""
        result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None
    ) -> Tuple[List[Task], int]:
        """Получение списка задач с пагинацией и фильтрацией"""
        query = select(Task)
        
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        
        # Получаем общее количество
        count_query = select(func.count()).select_from(Task)
        if status:
            count_query = count_query.where(Task.status == status)
        if priority:
            count_query = count_query.where(Task.priority == priority)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Получаем задачи с пагинацией
        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        return tasks, total
    
    async def update_task(
        self,
        task_id: int,
        update_data: TaskUpdate
    ) -> Optional[Task]:
        """Обновление задачи"""
        task = await self.get_task(task_id)
        if not task:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        
        # Обработка изменения статуса
        if 'status' in update_dict:
            new_status = TaskStatus(update_dict['status'])
            
            if new_status == TaskStatus.IN_PROGRESS and not task.started_at:
                update_dict['started_at'] = datetime.utcnow()
            
            if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if not task.completed_at:
                    update_dict['completed_at'] = datetime.utcnow()
        
        await self.db.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(**update_dict)
        )
        await self.db.commit()
        
        # Получаем обновленную задачу
        return await self.get_task(task_id)
    
    async def cancel_task(self, task_id: int) -> Optional[Task]:
        """Отмена задачи"""
        task = await self.get_task(task_id)
        if not task or task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return None
        
        update_data = TaskUpdate(
            status=TaskStatus.CANCELLED,
            error_info="Task cancelled by user"
        )
        return await self.update_task(task_id, update_data)
    
    async def delete_task(self, task_id: int) -> bool:
        """Удаление задачи"""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        await self.db.delete(task)
        await self.db.commit()
        return True
