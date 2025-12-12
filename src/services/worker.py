import asyncio
import json
from datetime import datetime
import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models.task import Task, TaskStatus
from services.task_service import TaskService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskWorker:
    def __init__(self):
        self.engine = create_async_engine(settings.async_database_url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def process_task(self, task_id: int):
        """Обработка задачи (имитация долгой операции)"""
        async with self.async_session() as session:
            task_service = TaskService(session)
            
            # Обновляем статус на IN_PROGRESS
            from api.v1.schemas import TaskUpdate
            await task_service.update_task(
                task_id,
                TaskUpdate(status=TaskStatus.IN_PROGRESS)
            )
            
            # Имитация обработки задачи
            try:
                logger.info(f"Processing task {task_id}")
                
                # Имитация различной длительности обработки в зависимости от приоритета
                task = await task_service.get_task(task_id)
                if task.priority.value == "high":
                    await asyncio.sleep(1)  # Быстрая обработка для высокого приоритета
                elif task.priority.value == "medium":
                    await asyncio.sleep(3)
                else:
                    await asyncio.sleep(5)  # Медленная обработка для низкого приоритета
                
                # Успешное завершение
                result = f"Task {task_id} processed successfully at {datetime.utcnow().isoformat()}"
                await task_service.update_task(
                    task_id,
                    TaskUpdate(
                        status=TaskStatus.COMPLETED,
                        result=result
                    )
                )
                logger.info(f"Task {task_id} completed successfully")
                
            except Exception as e:
                # Ошибка при обработке
                error_msg = f"Error processing task {task_id}: {str(e)}"
                await task_service.update_task(
                    task_id,
                    TaskUpdate(
                        status=TaskStatus.FAILED,
                        error_info=error_msg
                    )
                )
                logger.error(f"Task {task_id} failed: {str(e)}")
    
    async def consume_tasks(self):
        """Потребление задач из очереди RabbitMQ"""
        connection = await aio_pika.connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASSWORD
        )
        
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)  # Обрабатываем до 10 задач параллельно
            
            queue = await channel.declare_queue(
                settings.RABBITMQ_QUEUE,
                durable=True
            )
            
            logger.info("Worker started. Waiting for tasks...")
            
            async for message in queue:
                async with message.process():
                    try:
                        task_data = json.loads(message.body.decode())
                        task_id = task_data.get("task_id")
                        
                        if task_id:
                            await self.process_task(task_id)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding message: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")


async def main():
    worker = TaskWorker()
    await worker.consume_tasks()


if __name__ == "__main__":
    asyncio.run(main())
