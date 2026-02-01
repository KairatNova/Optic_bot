# tests/conftest.py
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from database.base import Base

@pytest.fixture(scope="session")  # одна база на все тесты
def db_session():
    engine = create_engine("sqlite:///test_db.sqlite")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Создаём схему только один раз
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # НЕ откатываем и НЕ закрываем агрессивно — данные остаются
    session.commit()  # сохраняем всё, что не было закоммичено
    session.close()