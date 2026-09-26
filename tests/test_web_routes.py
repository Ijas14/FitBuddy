import pytest
from fastapi.testclient import TestClient

import app.routes as routes
from app.gemini_error import GeminiError
from app.main import app
from app.database import Base, engine, save_user, save_plan, get_user, get_original_plan

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


PLAN = "Day 1:\nWarm-up: jumping jacks\nMain Workout: squats 3x10\nCooldown: stretch"


@pytest.fixture
def mock_generators(monkeypatch):
    """Replace both generators so web tests never depend on a live Gemini."""
    monkeypatch.setattr(routes, "generate_workout_gemini", lambda data: PLAN)
    monkeypatch.setattr(routes, "generate_nutrition_tip_with_flash", lambda goal: "Eat protein after workouts.")
    monkeypatch.setattr(routes, "update_workout_plan", lambda original, feedback: f"{original}\n[Revised: {feedback}]")


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "FitBuddy" in response.text
    assert "Generate Plan" in response.text


def test_form_generate_workout(mock_generators):
    form_data = {
        "username": "WebUser",
        "user_id": 50,
        "age": 24,
        "weight": 65.0,
        "goal": "weight loss",
        "intensity": "high",
    }
    response = client.post("/generate-workout", data=form_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "WebUser" in response.text
    assert "50" in response.text
    assert "Workout Plan" in response.text
    assert "Nutrition Tip" in response.text
    assert "Eat protein after workouts." in response.text

    # Verify database persistence
    user = get_user(50)
    assert user is not None
    assert user.name == "WebUser"
    plan = get_original_plan(50)
    assert plan is not None
    assert len(plan) > 50


def test_form_generate_workout_shows_exact_reason_on_failure(monkeypatch):
    """A failed Gemini call renders the styled error page with the reason."""

    def boom(data):
        raise GeminiError("Gemini quota exceeded (HTTP 429): limit 20 requests per day")

    monkeypatch.setattr(routes, "generate_workout_gemini", boom)
    response = client.post(
        "/generate-workout",
        data={
            "username": "WebUser",
            "user_id": 51,
            "age": 24,
            "weight": 65.0,
            "goal": "weight loss",
            "intensity": "high",
        },
    )
    assert response.status_code == 502
    assert "text/html" in response.headers["content-type"]
    assert "Workout plan could not be generated" in response.text
    assert "Gemini quota exceeded (HTTP 429)" in response.text
    # Nothing persisted — no half-registered user.
    assert get_user(51) is None


def test_form_generate_workout_keeps_plan_when_tip_fails(monkeypatch):
    def boom(goal):
        raise GeminiError("Gemini quota exceeded (HTTP 429): limit 20 requests per day")

    monkeypatch.setattr(routes, "generate_workout_gemini", lambda data: PLAN)
    monkeypatch.setattr(routes, "generate_nutrition_tip_with_flash", boom)
    response = client.post(
        "/generate-workout",
        data={
            "username": "WebUser",
            "user_id": 52,
            "age": 24,
            "weight": 65.0,
            "goal": "weight loss",
            "intensity": "high",
        },
    )
    assert response.status_code == 200
    assert "Workout Plan" in response.text
    assert "Nutrition tip could not be generated" in response.text
    assert "Gemini quota exceeded (HTTP 429)" in response.text
    assert get_original_plan(52) is not None


def test_form_submit_feedback(mock_generators):
    save_user(55, "FeedbackGuy", 29, 78.0, "muscle gain", "medium")
    save_plan(55, "Original bench and squat plan")

    form_data = {
        "user_id": 55,
        "feedback": "Include 15 minutes of core exercises each day",
    }
    response = client.post("/submit-feedback", data=form_data)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Your plan has been updated based on your feedback!" in response.text
    assert "FeedbackGuy" in response.text


def test_form_submit_feedback_unknown_user_is_styled_404():
    """Regression: this used to dump the browser onto bare JSON."""
    response = client.post("/submit-feedback", data={"user_id": 424242, "feedback": "anything"})
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "User not found" in response.text
    assert "424242" in response.text


def test_form_submit_feedback_ai_failure_keeps_original_plan(monkeypatch):
    save_user(56, "RevisionUser", 30, 80.0, "muscle gain", "high")
    save_plan(56, "Original Day 1 to 7 plan")

    def boom(original, feedback):
        raise GeminiError("Model or resource not found (HTTP 404): gemini-9.9-pro retired")

    monkeypatch.setattr(routes, "update_workout_plan", boom)
    response = client.post("/submit-feedback", data={"user_id": 56, "feedback": "more cardio"})
    assert response.status_code == 502
    assert "Plan could not be revised" in response.text
    assert "gemini-9.9-pro retired" in response.text
    assert "original plan is unchanged" in response.text
    # The stored plan was not touched by the failed revision.
    assert get_original_plan(56) == "Original Day 1 to 7 plan"


def test_view_all_users_dashboard(mock_generators):
    save_user(60, "AdminSeenUser", 22, 55.0, "muscle gain", "high")
    save_plan(60, "Plan for Admin inspection")

    response = client.get("/view-all-users")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AdminSeenUser" in response.text
    assert "FitBuddy - All Users" in response.text


def test_delete_user_route():
    save_user(70, "UserToBeDeleted", 33, 70.0, "flexibility", "low")
    save_plan(70, "Disposable plan")

    response = client.post("/delete-user/70")
    assert response.status_code in [200, 303, 302]

    # Verify user is gone
    assert get_user(70) is None
