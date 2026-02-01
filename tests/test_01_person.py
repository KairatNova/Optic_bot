import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError
from database.models import Person, Vision
from sqlalchemy.orm import Session


def test_create_person_basic(db_session: Session):
    person = Person(
        phone="+79990000001",  # уникальный
        first_name="Иван",
        last_name="Петров",
        age=30,
    )

    db_session.add(person)
    db_session.commit()

    fetched = db_session.get(Person, person.id)
    assert fetched is not None
    assert fetched.phone == "+79990000001"
    assert fetched.first_name == "Иван"
    assert fetched.last_name == "Петров"
    assert fetched.age == 30
    assert fetched.role == "client"
    assert isinstance(fetched.created_at, datetime)
    assert isinstance(fetched.updated_at, datetime)


def test_person_full_name_computed(db_session: Session):
    cases = [
        ("Иван", "Петров", "Иван Петров"),
        ("Анна", None, "Анна"),
        (None, "Сидорова", "Сидорова"),
        (None, None, ""),
        (" Мария ", "  Иванова  ", "Мария Иванова"),
    ]

    base_phone = 100  # чтобы не пересекаться с другими тестами
    for i, (first, last, expected) in enumerate(cases):
        person = Person(
            phone=f"+79990000{base_phone + i}",  # уникальные: +79990000100, +79990000101 и т.д.
            first_name=first,
            last_name=last,
        )
        db_session.add(person)
        db_session.commit()
        db_session.refresh(person)

        assert person.full_name == expected


def test_unique_constraints(db_session: Session):
    p1 = Person(phone="+79990000010", telegram_id=123456789)  # уникальный
    db_session.add(p1)
    db_session.commit()

    # Дубликат phone
    p2 = Person(phone="+79990000010")
    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()  # <<< чиним сессию!

    # Дубликат telegram_id
    p3 = Person(phone="+79990000011", telegram_id=123456789)
    db_session.add(p3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()  # <<< чиним сессию!


def test_person_vision_relationship(db_session: Session):
    person = Person(phone="+79990000020", first_name="Алексей")  # уникальный
    db_session.add(person)
    db_session.commit()

    vision1 = Vision(
        person_id=person.id,
        visit_date=date(2025, 1, 15),
        sph_r=-1.5,
        cyl_r=-0.75,
        axis_r=90,
        pd=62.0,
        note="Первичный осмотр",
    )
    vision2 = Vision(
        person_id=person.id,
        visit_date=date(2025, 6, 20),
        sph_l=-2.0,
        cyl_l=-1.0,
        axis_l=180,
    )

    db_session.add_all([vision1, vision2])
    db_session.commit()

    db_session.refresh(person)
    assert len(person.visions) == 2
    assert person.visions[0].note == "Первичный осмотр"

    fetched_vision = db_session.get(Vision, vision1.id)
    assert fetched_vision.person.id == person.id # type: ignore
    assert fetched_vision.person.first_name == "Алексей" # type: ignore


def test_cascade_delete(db_session: Session):
    person = Person(phone="+79990000030")  # уникальный
    db_session.add(person)
    db_session.commit()

    vision = Vision(person_id=person.id, visit_date=date.today())
    db_session.add(vision)
    db_session.commit()

    db_session.delete(person)
    db_session.commit()

    assert db_session.get(Vision, vision.id) is None


def test_required_fields(db_session: Session):
    # phone обязателен
    person = Person()  # без phone
    db_session.add(person)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()  # <<< чиним сессию!

    # role имеет дефолт — ок
    person = Person(phone="+79990000040")  # уникальный
    db_session.add(person)
    db_session.commit()
    assert person.role == "client"