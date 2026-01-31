from datetime import date, datetime
from sqlalchemy import Boolean, Column, Computed, Date, DateTime, Float, Index, Integer, String, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database.base import Base


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    telegram_id: Mapped[int | None] = mapped_column(
        Integer,
        unique=True,
        nullable=True,
        index=True
    )

    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # SQLite computed column
    full_name: Mapped[str] = mapped_column(
        String,
        Computed(
            "TRIM(IFNULL(first_name, '') || ' ' || IFNULL(last_name, ''))",
            persisted=True
        )
    )

    phone: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    role: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="client",
        index=True
    )

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

    last_visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # 🔹 ОДИН → МНОГИЕ
    visions: Mapped[list["Vision"]] = relationship(
        "Vision",
        back_populates="person",
        cascade="all, delete-orphan"
    )

class Vision(Base):
    __tablename__ = "visions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    sph_r: Mapped[float | None] = mapped_column(Float, nullable=True)
    cyl_r: Mapped[float | None] = mapped_column(Float, nullable=True)
    axis_r: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sph_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    cyl_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    axis_l: Mapped[int | None] = mapped_column(Integer, nullable=True)

    pd: Mapped[float | None] = mapped_column(Float, nullable=True)
    lens_type: Mapped[str | None] = mapped_column(String, nullable=True)
    frame_model: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    person: Mapped["Person"] = relationship(
        "Person",
        back_populates="visions"
    )


