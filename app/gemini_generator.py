"""Gemini Pro workout-plan generation, plus the shared Gemini error handling.

The DOCX project tree lists no separate error module, so `GeminiError` and the
reason-extraction helpers live here and the other two generators import them
from this module. With no offline fallback, every generator raises instead of
returning canned text; the reason is surfaced verbatim by the callers.
"""

import os
import re

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


# --- structured view of a failure -------------------------------------------
# Google's error strings carry the useful facts (status, model, quota metric,
# limit, retry delay) inside a protobuf dump. The templates show the parsed
# view and keep the raw text behind a <details>, so nothing is hidden.

_STATUS_RE = re.compile(r"\b([45]\d\d)\b")
_MODEL_RE = re.compile(r'model:\s*["\']?([A-Za-z0-9._-]+)')
_METRIC_RE = re.compile(r"Quota exceeded for metric:\s*([\w./-]+)")
_LIMIT_RE = re.compile(r"limit:\s*(\d+)")
_QUOTA_ID_RE = re.compile(r'quota_id:\s*"([^"]+)"')
_RETRY_RE = re.compile(r"[Pp]lease retry in\s*([0-9.]+)\s*s|retry_delay \{\s*seconds:\s*(\d+)")


def _quota_window(quota_id: str) -> str:
    """`GenerateRequestsPerDayPerProjectPerModel-FreeTier` -> 'per day, per project, per model (free tier)'."""
    if not quota_id:
        return ""
    body, _, tier = quota_id.partition("-")
    parts = []
    for token, phrase in (("PerMinute", "per minute"), ("PerDay", "per day"),
                          ("PerProject", "per project"), ("PerModel", "per model")):
        if token in body:
            parts.append(phrase)
    if not parts:
        parts.append(quota_id)
    if "FreeTier" in tier:
        parts.append("free tier")
    return ", ".join(parts)


def explain_failure(reason: str, model: str = "") -> dict:
    """Parse a failure reason into what a person needs to see and act on.

    Returns a dict with ``kind``, ``status``, ``headline``, ``detail``,
    ``actions`` and ``facts`` (label/value pairs), plus the untouched ``raw``.
    """
    raw = " ".join((reason or "").split())
    status_match = _STATUS_RE.search(raw)
    status = int(status_match.group(1)) if status_match else None

    models = []
    for name in _MODEL_RE.findall(raw):
        if name not in models:
            models.append(name)
    if not models and model:
        models.append(model)
    metrics = []
    for metric in _METRIC_RE.findall(raw):
        if metric not in metrics:
            metrics.append(metric)
    limits = _LIMIT_RE.findall(raw)
    quota_ids = _QUOTA_ID_RE.findall(raw)
    retry = next((g for g in (m.group(1) or m.group(2) for m in _RETRY_RE.finditer(raw)) if g), None)

    limit_text = limits[0] if limits else None
    window = _quota_window(quota_ids[0]) if quota_ids else ""
    lowered = raw.lower()

    if "quota" in lowered or status == 429:
        kind = "quota"
        headline = "Gemini quota exhausted"
        if limit_text == "0" or (window and "free tier" in window):
            detail = ("This API key has no requests left for this model on its current plan. "
                      "Free-tier keys do not include Pro models at all.")
        else:
            detail = "This API key has used up its allowance for this model."
        actions = [
            "Enable billing on the project in Google AI Studio to lift the quota limits.",
            "Or point GEMINI_PRO_MODEL / GEMINI_FLASH_MODEL at a model that still has free quota.",
        ]
    elif status == 404 or "not found" in lowered or "no longer available" in lowered:
        kind = "model"
        headline = "Gemini does not recognise that model"
        detail = "The model name in your .env is unknown, retired, or not open to new users."
        actions = [
            "Check GEMINI_PRO_MODEL and GEMINI_FLASH_MODEL in .env against a current model id.",
            "Restart the server after editing .env.",
        ]
    elif status in (401, 403) or "api key" in lowered and "invalid" in lowered:
        kind = "auth"
        headline = "Gemini rejected the API key"
        detail = "The key is missing, malformed, or not allowed to use this model."
        actions = ["Put a valid GOOGLE_API_KEY in .env and restart the server."]
    elif "timed out" in lowered or "deadline" in lowered:
        kind = "timeout"
        headline = "Gemini did not answer in time"
        detail = "The generation call ran past its deadline."
        actions = ["Try again, or lower the size of the request."]
    elif status is not None and status >= 500:
        kind = "service"
        headline = "Gemini had a problem on its side"
        detail = f"Google returned a {status} from the generation service."
        actions = ["Try again in a moment."]
    elif "no text" in lowered or "blocked" in lowered or "empty" in lowered:
        kind = "empty"
        headline = "Gemini returned nothing usable"
        detail = "The call succeeded but produced no text, usually a safety block."
        actions = ["Rephrase the request, or try a different model."]
    else:
        kind = "unknown"
        headline = "The Gemini call failed"
        detail = "The request did not complete. The raw reason is below."
        actions = ["Check the raw reason below, then adjust your .env if it mentions a model or key."]

    facts = []
    if status:
        facts.append(("Status", f"HTTP {status}"))
    for name in models[:2]:
        facts.append(("Model", name))
    if limit_text is not None:
        limit_label = f"Limit ({window})" if window else "Limit"
        facts.append((limit_label, f"{limit_text} requests"))
    for metric in metrics[:2]:
        facts.append(("Quota metric", metric.rsplit("/", 1)[-1]))
    if retry:
        facts.append(("Retry after", f"{float(retry):.0f}s"))

    return {
        "kind": kind,
        "status": status,
        "headline": headline,
        "detail": detail,
        "actions": actions,
        "facts": facts,
        "raw": raw,
    }


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
