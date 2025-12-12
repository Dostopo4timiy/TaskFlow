import asyncio
import json
import aio_pika
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings
from src.models.task import TaskStatus
from src.services.task_service import TaskService
import random


class TaskWorker:
    def __init__(self):
        self.db_engine = create_async_engine(settings.database_url)
        self.async_session = async_sessionmaker(
            self.db_engine, expire_on_commit=False
        )
    
    async def process_task(self, task_id: int):
        """Обработка задачи (имитация длительной операции)"""
        async with self.async_session() as db:
            task_service = TaskService(db)
            
            # Обновляем статус на IN_PROGRESS
            await task_service.update_task_status(task_id, TaskStatus.IN_PROGRESS)
            
            try:
                # Имитация обработки задачи
                await asyncio.sleep(random.uniform(1, 5))
                
                # 90% успеха, 10% ошибки для демонстрации
                if random.random() < 0.9:
                    result = f"Task {task_id} completed successfully"
                    await task_service.update_task_status(
                        task_id,
                        TaskStatus.COMPLETED,
                        result=result
                    )
                else:
                    error_info = f"Task {task_id} failed due to random error"
                    await task_service.update_task_status(
                        task_id,
                        TaskStatus.FAILED,
                        error_info=error_info
                    )
                    
            except Exception as e:
                error_info = f"Task {task_id} failed: {str(e)}"
                await task_service.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    error_info=error_info
                )
    
    async def consume_tasks(self):
        """Потребление задач из очереди"""
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            
            queue = await channel.declare_queue(
                "task_queue",
                durable=True,
                arguments={"x-max-priority": 10}
            )
            
            async for message in queue:
                async with message.process():
                    try:
                        task_data = json.loads(message.body.decode())
                        task_id = task_data["task_id"]
                        
                        # Обновляем статус на PENDING перед обработкой
                        async with self.async_session() as db:
                            task_service = TaskService(db)
                            await task_service.update_task_status(
                                task_id, TaskStatus.PENDING
                            )
                        
                        # Обрабатываем задачу
                        await self.process_task(task_id)
                        
                    except Exception as e:
                        print(f"Error processing message: {e}")
    
    async def run(self):
        """Запуск воркера"""
        print("Task worker started...")
        await self.consume_tasks()
