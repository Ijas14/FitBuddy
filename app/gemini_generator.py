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
