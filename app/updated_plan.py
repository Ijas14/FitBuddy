import os
import google.generativeai as genai
from dotenv import load_dotenv
from app.gemini_error import GeminiError, no_model_reason, reason_from_exception, text_or_raise

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


def update_workout_plan(original_plan: str, user_feedback: str) -> str:
    """
    Use Gemini Pro to update the workout plan based on user feedback.

    Args:
        original_plan (str): The existing 7-day workout plan text.
        user_feedback (str): Feedback or requested revisions from the user.

    Returns:
        str: Revised plan text.

    Raises:
        GeminiError: With the exact reason when the client is unconfigured,
            the API call fails, or the model returns no usable text.
    """
    if model is None:
        raise GeminiError(no_model_reason())

    prompt = f"""
You are a professional fitness trainer assistant.

Here's the original 7-day workout plan:
{original_plan}

User Feedback:
"{user_feedback}"

Based on the feedback, revise the relevant parts of the workout plan. Keep the format and rest of the plan unchanged if not needed.
"""

    try:
        response = model.generate_content(prompt)
    except Exception as exc:
        raise GeminiError(reason_from_exception(exc)) from exc
    return text_or_raise(response, "updated plan")
