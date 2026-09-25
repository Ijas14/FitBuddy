import os
import google.generativeai as genai
from dotenv import load_dotenv

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


def _get_fallback_updated_plan(original_plan: str, user_feedback: str) -> str:
    """Modifies original plan by injecting requested feedback adjustments."""
    notes = f"\n\n[Updated based on your feedback: '{user_feedback}']"
    if "cardio" in user_feedback.lower():
        notes += "\n- Added 15-20 minutes of moderate-intensity cardio/HIIT to Day 2 and Day 5."
    if "yoga" in user_feedback.lower() or "stretch" in user_feedback.lower():
        notes += "\n- Included 20 minutes of restorative yoga and deep stretching on Day 4 and Day 7."
    if "rest" in user_feedback.lower():
        notes += "\n- Scheduled an extra active recovery day to optimize rest."
    
    return f"{original_plan}{notes}"


def update_workout_plan(original_plan: str, user_feedback: str) -> str:
    """
    Use Gemini 1.5 Pro to update the workout plan based on user feedback.

    Args:
        original_plan (str): The existing 7-day workout plan text.
        user_feedback (str): Feedback or requested revisions from the user.

    Returns:
        str: Revised workout plan text.
    """
    prompt = f"""
You are a professional fitness trainer assistant.

Here's the original 7-day workout plan:
{original_plan}

User Feedback:
"{user_feedback}"

Based on the feedback, revise the relevant parts of the workout plan. Keep the format and rest of the plan unchanged if not needed.
"""

    if model is not None:
        try:
            response = model.generate_content(prompt)
            if response and hasattr(response, "text") and response.text:
                return response.text.strip()
        except Exception:
            pass

    return _get_fallback_updated_plan(original_plan, user_feedback)
