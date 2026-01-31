from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///./database.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,        # лог SQL-запросов (на проде False)
    future=True
)


