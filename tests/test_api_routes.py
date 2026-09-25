import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, save_user, save_plan

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_api_generate_workout_gemini():
    response = client.post(
        "/generate-workout/gemini",
        json={"goal": "weight loss", "intensity": "high"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "gemini-pro"
    assert "workout_plan" in data
    assert len(data["workout_plan"]) > 50


def test_api_nutrition_tip():
    response = client.get("/nutrition-tip?goal=muscle%20gain")
    assert response.status_code == 200
    data = response.json()
    assert data["goal"] == "muscle gain"
    assert "nutrition_tip" in data
    assert len(data["nutrition_tip"]) > 20


def test_api_generate_plan_and_save():
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
    assert "message" in data
    assert "workout_plan" in data
    assert "generated and saved successfully" in data["message"].lower()


def test_api_update_plan():
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
    assert len(data["updated_plan"]) > 20


def test_api_update_plan_not_found():
    response = client.post(
        "/update-plan/9999",
        json={"feedback": "Non-existent user"},
    )
    assert response.status_code == 404 or "error" in response.json()
