import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    """Тест создания задачи"""
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "medium"
    }
    
    response = await client.post("/api/v1/tasks", json=task_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["description"] == task_data["description"]
    assert data["priority"] == task_data["priority"]
    assert data["status"] == "new"


@pytest.mark.asyncio
async def test_get_tasks(client: AsyncClient):
    """Тест получения списка задач"""
    response = await client.get("/api/v1/tasks")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "tasks" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, test_task):
    """Тест получения задачи по ID"""
    response = await client.get(f"/api/v1/tasks/{test_task['id']}")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["id"] == test_task["id"]
    assert data["title"] == test_task["title"]


@pytest.mark.asyncio
async def test_get_task_status(client: AsyncClient, test_task):
    """Тест получения статуса задачи"""
    response = await client.get(f"/api/v1/tasks/{test_task['id']}/status")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["task_id"] == test_task["id"]
    assert "status" in data
    assert "created_at" in data
