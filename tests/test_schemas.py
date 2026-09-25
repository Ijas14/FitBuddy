import pytest
from pydantic import ValidationError
from app.schemas import (
    UserInput,
    WorkoutRequest,
    FeedbackRequest,
    WorkoutResponse,
    NutritionResponse,
    PlanGenerationResponse,
)


def test_user_input_valid():
    data = {
        "user_id": 1,
        "username": "Alex",
        "age": 28,
        "weight": 72.5,
        "goal": "muscle gain",
        "intensity": "high",
    }
    user = UserInput(**data)
    assert user.user_id == 1
    assert user.username == "Alex"
    assert user.age == 28
    assert user.weight == 72.5
    assert user.goal == "muscle gain"
    assert user.intensity == "high"


def test_user_input_invalid_age():
    with pytest.raises(ValidationError):
        UserInput(
            user_id=1,
            username="Alex",
            age=-5,
            weight=70.0,
            goal="fat loss",
            intensity="medium",
        )


def test_workout_request_valid():
    req = WorkoutRequest(goal="weight loss", intensity="medium")
    assert req.goal == "weight loss"
    assert req.intensity == "medium"


def test_feedback_request_valid():
    fb = FeedbackRequest(feedback="Add more yoga")
    assert fb.feedback == "Add more yoga"


def test_response_models():
    w_resp = WorkoutResponse(model="gemini-pro", workout_plan="Plan text")
    assert w_resp.model == "gemini-pro"
    assert w_resp.workout_plan == "Plan text"

    n_resp = NutritionResponse(goal="muscle gain", nutrition_tip="Eat more protein")
    assert n_resp.goal == "muscle gain"
    assert n_resp.nutrition_tip == "Eat more protein"

    p_resp = PlanGenerationResponse(message="Success", workout_plan="Plan text")
    assert p_resp.message == "Success"
    assert p_resp.workout_plan == "Plan text"
