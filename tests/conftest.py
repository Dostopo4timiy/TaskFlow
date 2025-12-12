import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.main import app
from src.core.database import get_db
from src.models.task import Base
from src.core.config import settings


# Тестовая база данных
TEST_DATABASE_URL = settings.async_database_url.replace("taskdb", "taskdb_test")

# Асинхронный движок для тестов
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestAsyncSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Переопределенная зависимость для тестовой БД"""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Переопределяем зависимость
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Фикстура для event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def prepare_database() -> AsyncGenerator[None, None]:
    """Подготовка тестовой БД перед каждым тестом"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для тестового клиента"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для тестовой сессии БД"""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def test_task(client: AsyncClient) -> dict:
    """Фикстура для создания тестовой задачи"""
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "medium"
    }
    
    response = await client.post("/api/v1/tasks", json=task_data)
    return response.json()
