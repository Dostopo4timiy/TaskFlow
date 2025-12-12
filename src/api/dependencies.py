from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db as get_db_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async for session in get_db_session():
        yield session
