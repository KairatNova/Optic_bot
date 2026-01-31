from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import async_sessionmaker

from .engine import async_engine

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
