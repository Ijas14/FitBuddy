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


def _get_fallback_workout_plan(goal: str, intensity: str) -> str:
    """Deterministic, structured 7-day workout plan used when Gemini API is unconfigured or unreachable."""
    g = goal.lower()
    i = intensity.capitalize()
    return f"""## 7-Day {i} Intensity Workout Plan for {goal.title()}

This plan focuses on balanced full-body conditioning, structured progression, and safe recovery to help you achieve your goal of **{goal}**.

Day 1:
Warm-up: 5-10 mins light jogging, arm circles, leg swings, and dynamic torso twists.
Main Workout:
- Barbell Squats / Goblet Squats: 3 sets of 10-12 reps
- Push-ups / Bench Press: 3 sets of 8-12 reps
- Bent-over Rows: 3 sets of 10-12 reps
- Plank Hold: 3 sets of 45-60 seconds
Cooldown: 5 mins static hamstring, chest, and shoulder stretches.

Day 2:
Warm-up: 5-10 mins jumping jacks, high knees, and bodyweight air squats.
Main Workout:
- Romanian Deadlifts: 3 sets of 10-12 reps
- Overhead Dumbbell Press: 3 sets of 10-12 reps
- Walking Lunges: 3 sets of 12 reps per leg
- Lat Pulldowns or Pull-ups: 3 sets of 8-10 reps
Cooldown: 5 mins foam rolling quads and lower back stretches.

Day 3:
Warm-up: 5 mins brisk walking or jump rope and mobility drills.
Main Workout (Cardio & Core):
- HIIT Intervals / Incline Treadmill: 20 minutes (30s sprint, 60s walk)
- Mountain Climbers: 3 sets of 30 seconds
- Russian Twists: 3 sets of 20 reps per side
- Bicycle Crunches: 3 sets of 15 reps per side
Cooldown: 5-10 mins deep diaphragmatic breathing and child's pose.

Day 4:
Warm-up: 5 mins gentle dynamic mobility work.
Main Workout (Active Recovery & Mobility):
- 30-45 minutes light walking, swimming, or restorative yoga
- Hip flexor stretches, pigeon pose, cat-cow flow
Cooldown: 10 mins full-body foam rolling and gentle relaxation.

Day 5:
Warm-up: 5-10 mins rowing machine or arm circles and high knees.
Main Workout:
- Incline Dumbbell Press: 3 sets of 10-12 reps
- Dumbbell Bicep Curls: 3 sets of 12-15 reps
- Triceps Rope Pushdowns: 3 sets of 12-15 reps
- Lateral Shoulder Raises: 3 sets of 15 reps
- Hanging Knee Raises: 3 sets of 12 reps
Cooldown: 5 mins upper body static stretches (triceps, lats, chest).

Day 6:
Warm-up: 5-10 mins light cycling and dynamic lower body mobility.
Main Workout:
- Leg Press or Front Squats: 3 sets of 10-12 reps
- Hamstring Curls: 3 sets of 12-15 reps
- Calf Raises: 4 sets of 15-20 reps
- Cable Woodchoppers: 3 sets of 15 reps per side
Cooldown: 5 mins quad and glute stretches.

Day 7:
Warm-up: None required.
Main Workout (Rest & Regeneration):
- Dedicated rest day. Hydrate, take a scenic leisurely walk if desired.
Cooldown: 10 mins relaxing stretches and prioritizing 8+ hours of restorative sleep."""


def generate_workout_gemini(user_input: dict) -> str:
    """
    Generates a personalized 7-day workout plan using Gemini 1.5 Pro.
    Falls back gracefully to a deterministic plan if the API key is not configured or fails.
    """
    goal = user_input.get("goal", "general fitness")
    intensity = user_input.get("intensity", "medium")

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

    if model is not None:
        try:
            response = model.generate_content(prompt)
            if response and hasattr(response, "text") and response.text:
                return response.text.strip()
        except Exception:
            pass

    return _get_fallback_workout_plan(goal, intensity)
