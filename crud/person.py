from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Person


async def get_person_by_telegram_id(
    session: AsyncSession,
    telegram_id: int
) -> Person | None:
    result = await session.execute(
        select(Person).where(Person.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_client_if_not_exists(
    session: AsyncSession,
    telegram_id: int,
    username: str | None
) -> Person:
    person = await get_person_by_telegram_id(session, telegram_id)

    if person:
        return person

    person = Person(
        telegram_id=telegram_id,
        username=username,
        role="client",
    )

    session.add(person)
    await session.commit()
    await session.refresh(person)

    return person
