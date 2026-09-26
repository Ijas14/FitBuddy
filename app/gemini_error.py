"""Typed error for Gemini calls, with the exact failure reason preserved.

Every generator raises :class:`GeminiError` instead of silently degrading, so
callers (HTML routes, JSON API) can surface *why* the model call failed —
quota exhaustion, bad key, retired model name, network failure, or a blocked
or empty response — instead of showing model-shaped template text.
"""

from __future__ import annotations

# Maps google-api-core exception class names to a human prefix. The full
# upstream message (which already carries status codes, quota metric names and
# retry hints) is always appended, so nothing is lost.
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
