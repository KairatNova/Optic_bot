import pytest
from datetime import date

from database.models import Person


@pytest.mark.asyncio
async def test_create_person(session):
    person = Person(
        telegram_id=123456,
        first_name="Kairat",
        last_name="Nova",
        phone="+996700000000",
        age=25,
    )

    session.add(person)
    await session.commit()
    await session.refresh(person)

    assert person.id is not None
    assert person.full_name == "Kairat Nova"
    assert person.role == "client"


@pytest.mark.asyncio
async def test_unique_phone_constraint(session):
    p1 = Person(phone="+996700000001")
    p2 = Person(phone="+996700000001")

    session.add(p1)
    await session.commit()

    session.add(p2)

    with pytest.raises(Exception):
        await session.commit()
