import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.core.database import Base, get_db


# Тестовая БД
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test_db"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_task():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/tasks/",
            json={
                "name": "Test Task",
                "description": "Test Description",
                "priority": "HIGH"
            }
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Task"
    assert data["status"] == "NEW"


@pytest.mark.asyncio
async def test_get_tasks():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Создаем задачу
        await ac.post(
            "/api/v1/tasks/",
            json={"name": "Test Task", "priority": "MEDIUM"}
        )
        
        # Получаем список
        response = await ac.get("/api/v1/tasks/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["total"] == 1
