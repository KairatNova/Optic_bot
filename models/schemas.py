from datetime import date, datetime
from sqlalchemy import Column, Computed, Date, DateTime, Index, Integer, String, ForeignKey, func
from sqlalchemy.orm import relationship,  DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)  # может быть NULL, если клиент пришёл не через бот
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    # Реализация для SQLite
    full_name: Mapped[str] = mapped_column(String,
        Computed(
            "TRIM(IFNULL(first_name, '') || ' ' || IFNULL(last_name, ''))",
            persisted=True # Это превратит колонку в STORED
        ))
    phone: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)  # основной идентификатор клиента         
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False, default='client')  # 'client', 'employee', 'admin'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_visit_date: Mapped[date] = mapped_column(Date, nullable=True)


class VisionDate(Base):
    __tablename__ = "vision_dates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)




"""CREATE TABLE vision_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    visit_date      DATE NOT NULL,
    sph_r           REAL,
    cyl_r           REAL,
    axis_r          INTEGER,
    sph_l           REAL,
    cyl_l           REAL,
    axis_l          INTEGER,
    pd              REAL,
    lens_type       TEXT,
    frame_model     TEXT,
    note            TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_id   INTEGER REFERENCES persons(id)     -- кто внёс (сотрудник)
);"""


__table_args__ = (
    Index("ix_persons_phone", "phone"))