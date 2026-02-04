# services/content.py
from sqlalchemy import select
from typing import Dict

from database.models import BotContent
from database.session import AsyncSessionLocal

# Глобальный кэш
_content_cache: Dict[str, str] | None = None

async def _load_content() -> Dict[str, str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(BotContent))
        rows = result.scalars().all()
        return {row.key: row.value for row in rows}

async def get_bot_content(force_refresh: bool = False) -> Dict[str, str]:
    global _content_cache
    if force_refresh or _content_cache is None:
        _content_cache = await _load_content()
    return _content_cache

async def get_content(key: str, default: str = "Информация временно недоступна") -> str:
    content = await get_bot_content()
    return content.get(key, default)

def clear_content_cache() -> None:
    global _content_cache
    _content_cache = None