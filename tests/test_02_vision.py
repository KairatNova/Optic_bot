import pytest
from datetime import date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models import Person, Vision


def test_create_vision_basic(db_session: Session):
    # Уникальный телефон для этого теста
    person = Person(phone="+79990000001", first_name="Иван", last_name="Иванов")
    db_session.add(person)
    db_session.commit()

    vision = Vision(
        person_id=person.id,
        visit_date=date(2025, 2, 1),
        sph_r=-1.5,
        cyl_r=-0.75,
        axis_r=90,
        sph_l=-2.0,
        cyl_l=-1.0,
        axis_l=180,
        pd=62.5,
        lens_type="прогрессивные",
        frame_model="Ray-Ban RB2132",
        note="Первичный осмотр, жалобы на даль",
    )

    db_session.add(vision)
    db_session.commit()

    fetched = db_session.get(Vision, vision.id)
    assert fetched is not None
    assert fetched.person_id == person.id
    assert fetched.visit_date == date(2025, 2, 1)
    assert fetched.sph_r == -1.5
    assert fetched.cyl_r == -0.75
    assert fetched.axis_r == 90
    assert fetched.sph_l == -2.0
    assert fetched.pd == 62.5
    assert fetched.lens_type == "прогрессивные"
    assert fetched.frame_model == "Ray-Ban RB2132"
    assert fetched.note == "Первичный осмотр, жалобы на даль"
    assert isinstance(fetched.created_at, datetime)


def test_vision_required_fields(db_session: Session):
    # Уникальный телефон
    person = Person(phone="+79990000002")
    db_session.add(person)
    db_session.commit()

    # 1. Без visit_date
    vision1 = Vision(person_id=person.id)
    db_session.add(vision1)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 2. Без person_id
    vision2 = Vision(visit_date=date.today())
    db_session.add(vision2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Несуществующий person_id
    vision3 = Vision(person_id=999999, visit_date=date.today())
    db_session.add(vision3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_vision_nullable_fields(db_session: Session):
    # Уникальный телефон
    person = Person(phone="+79990000003")
    db_session.add(person)
    db_session.commit()

    vision = Vision(
        person_id=person.id,
        visit_date=date(2025, 3, 15),
    )

    db_session.add(vision)
    db_session.commit()
    db_session.refresh(vision)

    assert vision.sph_r is None
    assert vision.cyl_r is None
    assert vision.axis_r is None
    assert vision.sph_l is None
    assert vision.cyl_l is None
    assert vision.axis_l is None
    assert vision.pd is None
    assert vision.lens_type is None
    assert vision.frame_model is None
    assert vision.note is None


def test_vision_back_relationship(db_session: Session):
    # Уникальный телефон
    person = Person(phone="+79990000004", first_name="Анна")
    db_session.add(person)
    db_session.commit()

    vision = Vision(
        person_id=person.id,
        visit_date=date(2025, 4, 10),
        sph_r=-0.5,
        note="Контрольный осмотр",
    )
    db_session.add(vision)
    db_session.commit()

    db_session.refresh(vision)
    assert vision.person.id == person.id
    assert vision.person.first_name == "Анна"

    db_session.refresh(person)
    assert len(person.visions) == 1
    assert person.visions[0].sph_r == -0.5
    assert person.visions[0].note == "Контрольный осмотр"


def test_multiple_visions_per_person(db_session: Session):
    # Уникальный телефон
    person = Person(phone="+79990000005")
    db_session.add(person)
    db_session.commit()

    vision1 = Vision(person_id=person.id, visit_date=date(2024, 1, 1))
    vision2 = Vision(person_id=person.id, visit_date=date(2025, 1, 1))

    db_session.add_all([vision1, vision2])
    db_session.commit()

    db_session.refresh(person)
    assert len(person.visions) == 2
    dates = {v.visit_date for v in person.visions}
    assert dates == {date(2024, 1, 1), date(2025, 1, 1)}