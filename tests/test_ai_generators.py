"""Unit tests for the Gemini generators and their error handling.

The generators have no offline fallback: without a usable Gemini client they
raise :class:`GeminiError` carrying the exact reason. The suite never touches
the network — ``conftest.py`` strips ``GOOGLE_API_KEY`` before these modules
are imported, and the success paths here monkeypatch the SDK call.
"""

import pytest

from app import gemini_generator, gemini_flash_generator, updated_plan
from app.gemini_error import GeminiError, no_model_reason, reason_from_exception, text_or_raise
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan


def test_generators_start_without_a_live_model():
    """The suite must never reach Gemini, whatever `.env` holds.

    `conftest.py` assigns an empty key rather than popping the name, because
    the `app.gemini_*` modules run `load_dotenv()` at import time and would
    otherwise restore a developer's real key.
    """
    for module in (gemini_generator, gemini_flash_generator, updated_plan):
        assert module.model is None, f"{module.__name__} built a live model"
        assert module.API_KEY == "", f"{module.__name__} saw an API key"


def test_generate_workout_raises_without_key():
    with pytest.raises(GeminiError) as excinfo:
        generate_workout_gemini({"goal": "weight loss", "intensity": "high"})
    assert "GOOGLE_API_KEY" in excinfo.value.reason


def test_generate_nutrition_tip_raises_without_key():
    with pytest.raises(GeminiError) as excinfo:
        generate_nutrition_tip_with_flash("muscle gain")
    assert "GOOGLE_API_KEY" in excinfo.value.reason


def test_update_plan_raises_without_key():
    with pytest.raises(GeminiError) as excinfo:
        update_workout_plan("Day 1: Heavy Bench Press", "Add more cardio")
    assert "GOOGLE_API_KEY" in excinfo.value.reason


class ResourceExhausted(Exception):
    """Mimics google.api_core.exceptions.ResourceExhausted (same class name)."""
    code = 429


def test_reason_from_exception_maps_quota_error():
    exc = ResourceExhausted(
        "429 You exceeded your current quota. Quota metric: generate_content_free_tier_requests"
    )
    reason = reason_from_exception(exc)
    assert reason.startswith("Gemini quota exceeded (HTTP 429)")
    assert "generate_content_free_tier_requests" in reason


def test_reason_from_exception_keeps_unknown_details():
    exc = RuntimeError("connection reset by peer")
    reason = reason_from_exception(exc)
    assert reason.startswith("Gemini API call failed")
    assert "connection reset by peer" in reason


def _fake_response(text):
    class _Response:
        pass

    response = _Response()
    if isinstance(text, Exception):
        # Mimic google-generativeai: accessing .text on a blocked response raises.
        response.text = property(lambda self: (_ for _ in ()).throw(text))
        response.prompt_feedback = None
        response.candidates = []
    else:
        response.text = text
        response.prompt_feedback = None
        response.candidates = []
    return response


def test_text_or_raise_accepts_generated_text():
    assert text_or_raise(_fake_response("  Day 1: Squats  "), "workout plan") == "Day 1: Squats"


def test_text_or_raise_reports_empty_response():
    with pytest.raises(GeminiError) as excinfo:
        text_or_raise(_fake_response(""), "workout plan")
    assert "no text for the workout plan" in excinfo.value.reason
    assert "empty" in excinfo.value.reason


def test_text_or_raise_reports_blocked_response():
    with pytest.raises(GeminiError) as excinfo:
        text_or_raise(_fake_response(ValueError("blocked")), "nutrition tip")
    assert "no text for the nutrition tip" in excinfo.value.reason


def test_no_model_reason_names_the_variable():
    assert "GOOGLE_API_KEY" in no_model_reason()
