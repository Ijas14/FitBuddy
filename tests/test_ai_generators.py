import pytest
from app import gemini_generator, gemini_flash_generator, updated_plan
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan
from app.nutrition import get_quick_nutrition_guidance


def test_generators_are_forced_into_fallback_mode():
    """The suite must never reach Gemini, whatever `.env` holds.

    `conftest.py` assigns an empty key rather than popping the name, because
    the `app.gemini_*` modules run `load_dotenv()` at import time and would
    otherwise restore a developer's real key. Without this assertion the suite
    still passed while quietly calling the API, just ~25x slower.
    """
    for module in (gemini_generator, gemini_flash_generator, updated_plan):
        assert module.model is None, f"{module.__name__} built a live model"
        assert module.API_KEY == "", f"{module.__name__} saw an API key"


def test_generate_workout_gemini_fallback():
    user_input = {"goal": "weight loss", "intensity": "high"}
    plan = generate_workout_gemini(user_input)
    assert plan is not None
    assert len(plan) > 50
    assert "Day 1:" in plan
    assert "Day 7:" in plan
    assert "Warm-up" in plan
    assert "Main Workout" in plan
    assert "Cooldown" in plan


def test_generate_nutrition_tip_with_flash_fallback():
    tip = generate_nutrition_tip_with_flash("muscle gain")
    assert tip is not None
    assert len(tip) > 20
    assert "protein" in tip.lower() or "recovery" in tip.lower() or "muscle" in tip.lower() or "nutrition" in tip.lower()


def test_update_workout_plan_fallback():
    original = "Day 1: Heavy Bench Press\nDay 2: Squats"
    feedback = "Add more cardio and yoga"
    updated = update_workout_plan(original, feedback)
    assert updated is not None
    assert len(updated) > 20
    assert "cardio" in updated.lower() or "yoga" in updated.lower()


def test_nutrition_helper():
    guidance = get_quick_nutrition_guidance("weight loss")
    assert "hydration" in guidance.lower() or "calorie" in guidance.lower() or "deficit" in guidance.lower() or "protein" in guidance.lower()
