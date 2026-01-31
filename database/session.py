from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from .engine import engine

AsyncSessionLocal = sessionmaker(
    bind=engine,


)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session