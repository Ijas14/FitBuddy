import pytest
from fastapi.testclient import TestClient

import app.routes as routes
from app.gemini_error import GeminiError
from app.main import app
from app.database import Base, engine, save_user, save_plan

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


PLAN = "Day 1:\nWarm-up: jumping jacks\nMain Workout: squats 3x10\nCooldown: stretch"
REASON = "Gemini quota exceeded (HTTP 429): limit 20 requests per day"


@pytest.fixture
def mock_generators(monkeypatch):
    """Replace the generators so API tests never depend on a live Gemini."""
    monkeypatch.setattr(routes, "generate_workout_gemini", lambda data: PLAN)
    monkeypatch.setattr(routes, "generate_nutrition_tip_with_flash", lambda goal: "Eat protein after workouts.")
    monkeypatch.setattr(routes, "update_workout_plan", lambda original, feedback: f"{original}\n[Revised: {feedback}]")


def test_api_generate_workout_gemini(mock_generators):
    response = client.post(
        "/generate-workout/gemini",
        json={"goal": "weight loss", "intensity": "high"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "gemini-pro"
    assert data["workout_plan"] == PLAN


def test_api_generate_workout_gemini_failure_returns_exact_reason(monkeypatch):
    def boom(data):
        raise GeminiError(REASON)

    monkeypatch.setattr(routes, "generate_workout_gemini", boom)
    response = client.post(
        "/generate-workout/gemini",
        json={"goal": "weight loss", "intensity": "high"},
    )
    assert response.status_code == 502
    assert REASON in response.json()["detail"]


def test_api_nutrition_tip(mock_generators):
    response = client.get("/nutrition-tip?goal=muscle%20gain")
    assert response.status_code == 200
    data = response.json()
    assert data["goal"] == "muscle gain"
    assert data["nutrition_tip"] == "Eat protein after workouts."


def test_api_nutrition_tip_failure_returns_exact_reason(monkeypatch):
    def boom(goal):
        raise GeminiError(REASON)

    monkeypatch.setattr(routes, "generate_nutrition_tip_with_flash", boom)
    response = client.get("/nutrition-tip?goal=muscle%20gain")
    assert response.status_code == 502
    assert REASON in response.json()["detail"]


def test_api_generate_plan_and_save(mock_generators):
    payload = {
        "user_id": 101,
        "username": "Test User",
        "age": 27,
        "weight": 74.0,
        "goal": "general fitness",
        "intensity": "medium",
    }
    response = client.post("/generate-plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Workout plan generated and saved successfully!"
    assert data["workout_plan"] == PLAN


def test_api_generate_plan_failure_persists_nothing(monkeypatch):
    def boom(data):
        raise GeminiError(REASON)

    monkeypatch.setattr(routes, "generate_workout_gemini", boom)
    payload = {
        "user_id": 103,
        "username": "Never Saved",
        "age": 27,
        "weight": 74.0,
        "goal": "general fitness",
        "intensity": "medium",
    }
    response = client.post("/generate-plan", json=payload)
    assert response.status_code == 502
    assert REASON in response.json()["detail"]
    from app.database import get_user
    assert get_user(103) is None


def test_api_update_plan(mock_generators):
    save_user(
        user_id=102,
        name="Feedback User",
        age=30,
        weight=80.0,
        goal="muscle gain",
        intensity="high",
    )
    save_plan(user_id=102, plan="Original Day 1 to 7 plan")

    response = client.post(
        "/update-plan/102",
        json={"feedback": "Add more cardio sessions"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "updated_plan" in data
    assert "[Revised: Add more cardio sessions]" in data["updated_plan"]


def test_api_update_plan_not_found():
    """Spec'd behaviour: HTTP 200 with an `error` key when no plan exists."""
    response = client.post(
        "/update-plan/9999",
        json={"feedback": "Non-existent user"},
    )
    assert response.status_code == 200
    assert "error" in response.json()


def test_api_update_plan_ai_failure_returns_exact_reason(monkeypatch):
    save_user(user_id=104, name="RevUser", age=30, weight=80.0, goal="muscle gain", intensity="high")
    save_plan(user_id=104, plan="Original plan")

    def boom(original, feedback):
        raise GeminiError(REASON)

    monkeypatch.setattr(routes, "update_workout_plan", boom)
    response = client.post("/update-plan/104", json={"feedback": "more cardio"})
    assert response.status_code == 502
    assert REASON in response.json()["detail"]
