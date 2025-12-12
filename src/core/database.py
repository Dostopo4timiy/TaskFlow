from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator

from core.config import settings
from models.task import Base

# Создаем асинхронный движок
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        # Создаем таблицы
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Закрытие соединений с БД"""
    await engine.dispose()
