import pytest
from app.database import (
    Base,
    engine,
    SessionLocal,
    User,
    WorkoutPlan,
    save_user,
    save_plan,
    update_plan,
    get_original_plan,
    get_user,
    get_all_users,
    get_all_plans,
    delete_user,
)


@pytest.fixture(autouse=True)
def setup_teardown_db():
    """Provide a clean schema for each test against the isolated test DB."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_save_and_get_user():
    user = save_user(
        user_id=1,
        name="John Doe",
        age=25,
        weight=75.5,
        goal="muscle gain",
        intensity="high",
    )
    assert user.id == 1
    assert user.name == "John Doe"
    assert user.age == 25
    assert user.weight == 75.5
    assert user.goal == "muscle gain"
    assert user.intensity == "high"
    assert user.schedule == 7

    fetched = get_user(1)
    assert fetched is not None
    assert fetched.id == 1
    assert fetched.name == "John Doe"


def test_update_existing_user():
    save_user(
        user_id=2,
        name="Alice",
        age=30,
        weight=60.0,
        goal="weight loss",
        intensity="medium",
    )
    updated = save_user(
        user_id=2,
        name="Alice Smith",
        age=31,
        weight=58.5,
        goal="weight loss",
        intensity="high",
    )
    assert updated.id == 2
    assert updated.name == "Alice Smith"
    assert updated.age == 31
    assert updated.weight == 58.5
    assert updated.intensity == "high"


def test_save_and_get_original_plan():
    save_user(
        user_id=3,
        name="Bob",
        age=22,
        weight=68.0,
        goal="general fitness",
        intensity="low",
    )
    plan_text = "Day 1: Full body warm up and workout."
    plan = save_plan(user_id=3, plan=plan_text)
    assert plan.user_id == 3
    assert plan.original_plan == plan_text
    assert plan.updated_plan is None

    fetched_plan = get_original_plan(3)
    assert fetched_plan == plan_text


def test_update_plan_with_feedback():
    save_user(
        user_id=4,
        name="Charlie",
        age=28,
        weight=80.0,
        goal="muscle gain",
        intensity="high",
    )
    save_plan(user_id=4, plan="Original plan text")
    updated_text = "Updated plan with more cardio"
    updated_plan_obj = update_plan(user_id=4, updated_text=updated_text)

    assert updated_plan_obj is not None
    assert updated_plan_obj.updated_plan == updated_text
    assert updated_plan_obj.original_plan == "Original plan text"


def test_get_all_users_and_plans():
    save_user(
        user_id=10,
        name="User 10",
        age=20,
        weight=70.0,
        goal="weight loss",
        intensity="medium",
    )
    save_user(
        user_id=20,
        name="User 20",
        age=35,
        weight=85.0,
        goal="muscle gain",
        intensity="high",
    )
    save_plan(user_id=10, plan="Plan 10")
    save_plan(user_id=20, plan="Plan 20")

    users = get_all_users()
    assert len(users) == 2
    user_ids = [u.id for u in users]
    assert 10 in user_ids and 20 in user_ids

    plans = get_all_plans()
    assert len(plans) == 2


def test_delete_user():
    save_user(
        user_id=99,
        name="ToDelete",
        age=40,
        weight=90.0,
        goal="flexibility",
        intensity="low",
    )
    save_plan(user_id=99, plan="Temporary plan")

    success = delete_user(99)
    assert success is True
    assert get_user(99) is None
    assert get_original_plan(99) is None
