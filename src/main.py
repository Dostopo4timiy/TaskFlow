from fastapi import FastAPI
from contextlib import asynccontextmanager
from alembic import command
from alembic.config import Config

from src.api.v1.endpoints import router as api_router
from src.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    # Создаем таблицы при старте
    async with engine.begin() as conn:
        # Можно использовать Alembic, но для простоты создадим таблицы
        from src.models.task import Base
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Cleanup
    await engine.dispose()


app = FastAPI(
    title="Task Management Service",
    description="Асинхронный сервис управления задачами",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
