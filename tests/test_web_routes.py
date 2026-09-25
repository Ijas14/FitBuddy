import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, save_user, save_plan, get_user, get_original_plan

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "FitBuddy" in response.text
    assert "Generate Plan" in response.text


def test_form_generate_workout():
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

    # Verify database persistence
    user = get_user(50)
    assert user is not None
    assert user.name == "WebUser"
    plan = get_original_plan(50)
    assert plan is not None
    assert len(plan) > 50


def test_form_submit_feedback():
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


def test_view_all_users_dashboard():
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
