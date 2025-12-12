from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.sql import func

from src.models.task import Task as TaskModel, TaskStatus, TaskPriority
from src.api.v1.schemas import TaskCreate
import aio_pika
import json
from src.core.config import settings


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_task(self, task_data: TaskCreate) -> TaskModel:
        """Создание задачи и отправка в очередь"""
        task = TaskModel(
            name=task_data.name,
            description=task_data.description,
            priority=task_data.priority,
            status=TaskStatus.NEW
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        # Отправка задачи в очередь
        await self._send_to_queue(task.id, task.priority)
        
        return task
    
    async def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Tuple[list[TaskModel], int]:
        """Получение задач с фильтрацией и пагинацией"""
        query = select(TaskModel)
        
        if status:
            query = query.where(TaskModel.status == status)
        if priority:
            query = query.where(TaskModel.priority == priority)
        
        # Подсчет общего количества
        count_query = select(func.count()).select_from(TaskModel)
        if status:
            count_query = count_query.where(TaskModel.status == status)
        if priority:
            count_query = count_query.where(TaskModel.priority == priority)
        
        total = (await self.db.execute(count_query)).scalar()
        
        # Пагинация
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(TaskModel.created_at.desc())
        
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        return tasks, total
    
    async def get_task(self, task_id: int) -> Optional[TaskModel]:
        """Получение задачи по ID"""
        query = select(TaskModel).where(TaskModel.id == task_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def cancel_task(self, task_id: int) -> bool:
        """Отмена задачи"""
        query = select(TaskModel).where(
            and_(
                TaskModel.id == task_id,
                TaskModel.status.in_([TaskStatus.NEW, TaskStatus.PENDING])
            )
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()
        
        if task:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            await self.db.commit()
            return True
        
        return False
    
    async def update_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        result: Optional[str] = None,
        error_info: Optional[str] = None
    ) -> bool:
        """Обновление статуса задачи"""
        update_data = {"status": status}
        
        if status == TaskStatus.IN_PROGRESS:
            update_data["started_at"] = datetime.utcnow()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            update_data["completed_at"] = datetime.utcnow()
        
        if result:
            update_data["result"] = result
        if error_info:
            update_data["error_info"] = error_info
        
        stmt = (
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(**update_data)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def _send_to_queue(self, task_id: int, priority: TaskPriority):
        """Отправка задачи в очередь RabbitMQ"""
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            
            # Создаем очередь с приоритетами
            await channel.declare_queue(
                "task_queue",
                durable=True,
                arguments={"x-max-priority": 10}
            )
            
            message_body = json.dumps({"task_id": task_id})
            priority_map = {
                TaskPriority.LOW: 1,
                TaskPriority.MEDIUM: 5,
                TaskPriority.HIGH: 10
            }
            
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    priority=priority_map[priority]
                ),
                routing_key="task_queue"
            )from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.sql import func

from src.models.task import Task as TaskModel, TaskStatus, TaskPriority
from src.api.v1.schemas import TaskCreate
import aio_pika
import json
from src.core.config import settings


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_task(self, task_data: TaskCreate) -> TaskModel:
        """Создание задачи и отправка в очередь"""
        task = TaskModel(
            name=task_data.name,
            description=task_data.description,
            priority=task_data.priority,
            status=TaskStatus.NEW
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        # Отправка задачи в очередь
        await self._send_to_queue(task.id, task.priority)
        
        return task
    
    async def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Tuple[list[TaskModel], int]:
        """Получение задач с фильтрацией и пагинацией"""
        query = select(TaskModel)
        
        if status:
            query = query.where(TaskModel.status == status)
        if priority:
            query = query.where(TaskModel.priority == priority)
        
        # Подсчет общего количества
        count_query = select(func.count()).select_from(TaskModel)
        if status:
            count_query = count_query.where(TaskModel.status == status)
        if priority:
            count_query = count_query.where(TaskModel.priority == priority)
        
        total = (await self.db.execute(count_query)).scalar()
        
        # Пагинация
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(TaskModel.created_at.desc())
        
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        return tasks, total
    
    async def get_task(self, task_id: int) -> Optional[TaskModel]:
        """Получение задачи по ID"""
        query = select(TaskModel).where(TaskModel.id == task_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def cancel_task(self, task_id: int) -> bool:
        """Отмена задачи"""
        query = select(TaskModel).where(
            and_(
                TaskModel.id == task_id,
                TaskModel.status.in_([TaskStatus.NEW, TaskStatus.PENDING])
            )
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()
        
        if task:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            await self.db.commit()
            return True
        
        return False
    
    async def update_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        result: Optional[str] = None,
        error_info: Optional[str] = None
    ) -> bool:
        """Обновление статуса задачи"""
        update_data = {"status": status}
        
        if status == TaskStatus.IN_PROGRESS:
            update_data["started_at"] = datetime.utcnow()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            update_data["completed_at"] = datetime.utcnow()
        
        if result:
            update_data["result"] = result
        if error_info:
            update_data["error_info"] = error_info
        
        stmt = (
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(**update_data)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def _send_to_queue(self, task_id: int, priority: TaskPriority):
        """Отправка задачи в очередь RabbitMQ"""
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            
            # Создаем очередь с приоритетами
            await channel.declare_queue(
                "task_queue",
                durable=True,
                arguments={"x-max-priority": 10}
            )
            
            message_body = json.dumps({"task_id": task_id})
            priority_map = {
                TaskPriority.LOW: 1,
                TaskPriority.MEDIUM: 5,
                TaskPriority.HIGH: 10
            }
            
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    priority=priority_map[priority]
                ),
                routing_key="task_queue"
            )
