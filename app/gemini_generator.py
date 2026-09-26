"""Gemini Pro workout-plan generation, plus the shared Gemini error handling.

The DOCX project tree lists no separate error module, so `GeminiError` and the
reason-extraction helpers live here and the other two generators import them
from this module. With no offline fallback, every generator raises instead of
returning canned text; the reason is surfaced verbatim by the callers.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

_REASON_PREFIXES = {
    "ResourceExhausted": "Gemini quota exceeded (HTTP 429)",
    "NotFound": "Model or resource not found (HTTP 404) — check the model name in .env",
    "InvalidArgument": "Gemini rejected the request (HTTP 400) — check the API key and model name",
    "Unauthenticated": "Authentication failed (HTTP 401) — GOOGLE_API_KEY is missing or invalid",
    "PermissionDenied": "Access denied (HTTP 403) — the key is not allowed to use this model",
    "FailedPrecondition": "Gemini API is not enabled for this project (HTTP 400)",
    "DeadlineExceeded": "Gemini call timed out (HTTP 504)",
    "Unavailable": "Gemini service unavailable (HTTP 503)",
    "ServiceUnavailable": "Gemini service unavailable (HTTP 503)",
    "InternalServerError": "Gemini internal error (HTTP 500)",
}


class GeminiError(Exception):
    """A Gemini generation call failed.

    ``reason`` is a single human-readable string carrying the exact cause,
    suitable for showing directly to an end user or an API consumer.
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def reason_from_exception(exc: Exception) -> str:
    """Turn any Gemini SDK exception into one actionable reason string."""
    prefix = _REASON_PREFIXES.get(type(exc).__name__, "Gemini API call failed")
    code = getattr(exc, "code", None)
    code_part = f" [HTTP {code}]" if isinstance(code, int) else ""
    detail = " ".join(str(exc).split())
    return f"{prefix}{code_part}: {detail}"


def no_model_reason() -> str:
    """Why the module-level model object is unusable before any call is made."""
    return (
        "GOOGLE_API_KEY is not set, so the Gemini client was never initialized. "
        "Add it to the .env file and restart the server."
    )


def text_or_raise(response, what: str) -> str:
    """Extract the generated text from a Gemini response, or raise with the reason.

    ``what`` names the artifact in user terms, e.g. "workout plan" or
    "nutrition tip", so the message reads naturally on the error page.
    """
    try:
        text = (response.text or "").strip()
    except Exception:
        text = ""
    if text:
        return text

    detail = _blocked_or_empty_detail(response)
    raise GeminiError(f"The model returned no text for the {what}. {detail}")


def _blocked_or_empty_detail(response) -> str:
    parts = []
    prompt_feedback = getattr(response, "prompt_feedback", None)
    block_reason = getattr(prompt_feedback, "block_reason", None)
    if block_reason:
        parts.append(f"the prompt was blocked (block_reason={block_reason})")
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        finish_reason = getattr(candidate, "finish_reason", None)
        # The SDK uses an enum whose `.name` is "STOP", "MAX_TOKENS", "SAFETY"…
        # while plain ints may appear when the proto is flattened; 1 == STOP.
        name = getattr(finish_reason, "name", finish_reason)
        if name not in (None, "STOP", "FINISH_REASON_UNSPECIFIED", 0, 1):
            parts.append(f"the candidate stopped early (finish_reason={name})")
    if not parts:
        parts.append("the response was empty")
    return " ".join(parts)



load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
MODEL_NAME = os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro")

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(MODEL_NAME)
    except Exception:
        model = None
else:
    model = None


def generate_workout_gemini(user_input: dict) -> str:
    """
    Generates a personalized 7-day workout plan using Gemini Pro.

    Args:
        user_input (dict): {"goal": str, "intensity": str}.

    Returns:
        str: Generated plan.

    Raises:
        GeminiError: With the exact reason when the client is unconfigured,
            the API call fails, or the model returns no usable text.
    """
    goal = user_input.get("goal", "general fitness")
    intensity = user_input.get("intensity", "medium")

    if model is None:
        raise GeminiError(no_model_reason())

    prompt = f"""
You are a professional fitness trainer.

Create a personalized, structured 7-day workout plan for someone with the goal of **{goal}**, and prefers **{intensity}
intensity** workouts.

Each day must include:
- A warm-up (5-10 mins)
- Main workout (targeted exercises, sets & reps)
- Cooldown or recovery tip

Format:
Day 1:
Warm-up: ...
Main Workout: ...
Cooldown: ...
(Repeat for Day 2-7)
"""

    try:
        response = model.generate_content(prompt)
    except Exception as exc:
        raise GeminiError(reason_from_exception(exc)) from exc
    return text_or_raise(response, "workout plan")
