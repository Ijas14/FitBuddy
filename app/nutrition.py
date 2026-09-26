"""Nutrition domain reference: goal classification and per-goal focus.

The DOCX project tree (`word/media/image2.png`) lists `app/nutrition.py` as
"Handles nutrition-specific logic (optional)". Live tips come from Gemini Flash
via `app/gemini_flash_generator.py`; nothing in this module substitutes for that
call. It holds the goal vocabulary the app reasons about, so matching a
free-text goal against the canonical names lives in one place instead of being
re-implemented wherever a goal string is inspected.
"""

WEIGHT_LOSS = "weight loss"
MUSCLE_GAIN = "muscle gain"
GENERAL_FITNESS = "general fitness"
FLEXIBILITY = "flexibility"
GENERAL = "general"

# Ordered so a more specific phrasing wins over a broader one.
_GOAL_KEYWORDS = (
    (MUSCLE_GAIN, ("muscle gain", "build muscle", "muscle building", "hypertrophy", "gain muscle")),
    (WEIGHT_LOSS, ("weight loss", "lose weight", "fat loss", "cutting", "lose fat")),
    (FLEXIBILITY, ("flexibility", "mobility", "stretching")),
    (GENERAL_FITNESS, ("general fitness", "general health", "endurance", "health")),
)

# Short, non-prescriptive emphasis recorded per goal, for prompts, docs and tests.
NUTRITION_FOCUS = {
    MUSCLE_GAIN: "protein at 1.6-2.2 g per kg of bodyweight, a slight surplus, simple carbs around training",
    WEIGHT_LOSS: "high protein to protect lean mass, a moderate calorie deficit, steady hydration",
    FLEXIBILITY: "anti-inflammatory foods, omega-3 fats, hydration and magnesium",
    GENERAL_FITNESS: "a balanced plate: mostly vegetables, whole grains, lean protein, healthy fats",
    GENERAL: "a balanced plate, regular hydration and consistent rest",
}


def classify_goal(goal: str) -> str:
    """Map a free-text fitness goal onto one of the canonical goal names.

    Unrecognised text maps to ``GENERAL`` rather than guessing at a specific
    goal, so callers can rely on the return value being one of the constants
    defined here.
    """
    text = (goal or "").strip().lower()
    for canonical, keywords in _GOAL_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return canonical
    return GENERAL


def nutrition_focus(goal: str) -> str:
    """Return the recorded nutrition emphasis for a goal, canonical or not."""
    return NUTRITION_FOCUS[classify_goal(goal)]
