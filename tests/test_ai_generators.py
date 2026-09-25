import pytest
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan
from app.nutrition import get_quick_nutrition_guidance


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
