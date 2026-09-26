import os
import google.generativeai as genai
from dotenv import load_dotenv
from app.gemini_error import GeminiError, no_model_reason, reason_from_exception, text_or_raise

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
MODEL_NAME = os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash")

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(MODEL_NAME)
    except Exception:
        model = None
else:
    model = None


def generate_nutrition_tip_with_flash(goal: str) -> str:
    """
    Generate a nutrition or recovery tip using Gemini Flash based on the user's fitness goal.

    Args:
        goal (str): User's fitness goal - 'weight loss', 'muscle gain', etc.

    Returns:
        str: Generated tip.

    Raises:
        GeminiError: With the exact reason when the client is unconfigured,
            the API call fails, or the model returns no usable text.
    """
    if model is None:
        raise GeminiError(no_model_reason())

    prompt = (
        f"Give one clear, helpful nutrition or recovery tip for someone focused on '{goal}'. "
        "The tip should be practical, friendly, and easy to understand."
    )

    try:
        response = model.generate_content(prompt)
    except Exception as exc:
        raise GeminiError(reason_from_exception(exc)) from exc
    return text_or_raise(response, "nutrition tip")
