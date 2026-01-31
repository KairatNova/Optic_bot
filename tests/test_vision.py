import pytest
from datetime import date

from database.models import Person, Vision


@pytest.mark.asyncio
async def test_person_has_many_visions(session):
    person = Person(phone="+996700000002")

    vision1 = Vision(
        visit_date=date.today(),
        sph_r=-1.0,
    )

    vision2 = Vision(
        visit_date=date.today(),
        sph_l=-2.0,
    )

    person.visions.append(vision1)
    person.visions.append(vision2)

    session.add(person)
    await session.commit()
    await session.refresh(person)

    assert len(person.visions) == 2


@pytest.mark.asyncio
async def test_cascade_delete_visions(session):
    person = Person(phone="+996700000003")

    vision = Vision(
        visit_date=date.today(),
        sph_r=-1.5,
    )

    person.visions.append(vision)
    session.add(person)
    await session.commit()

    await session.delete(person)
    await session.commit()

    result = await session.get(Vision, vision.id)
    assert result is None
