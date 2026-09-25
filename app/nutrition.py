"""Nutrition helper functions and goal-based guidelines."""

GOAL_NUTRITION_TIPS = {
    "weight loss": (
        "Prioritize lean protein and dietary fiber with every meal to maintain satiety and preserve muscle mass. "
        "Stay in a moderate, consistent caloric deficit (300-500 kcal), drink at least 2.5-3 liters of water daily, "
        "and replace sugary drinks with herbal tea or water."
    ),
    "muscle gain": (
        "Prioritize protein! Aim for 1.6 to 2.2 grams of protein per kilogram of body weight from quality sources like chicken, "
        "fish, eggs, Greek yogurt, or tofu. Ensure a slight caloric surplus with nutrient-dense complex carbs (oats, brown rice, sweet potatoes) "
        "and get 7-9 hours of restful sleep for optimal muscle hypertrophy."
    ),
    "general fitness": (
        "Focus on a colorful, balanced Mediterranean-style plate: half non-starchy vegetables, one quarter lean protein, "
        "and one quarter whole grains, complemented with healthy fats like avocados, olive oil, and nuts. "
        "Stay properly hydrated before and during training sessions."
    ),
    "flexibility": (
        "Focus on anti-inflammatory whole foods rich in omega-3 fatty acids (salmon, chia seeds, walnuts) and antioxidants (berries, leafy greens). "
        "Adequate hydration and magnesium-rich foods like pumpkin seeds and spinach promote joint lubrication and muscle elasticity."
    ),
}


def get_quick_nutrition_guidance(goal: str) -> str:
    """Return tailored nutritional advice according to the user's fitness goal."""
    clean_goal = goal.strip().lower()
    for key, tip in GOAL_NUTRITION_TIPS.items():
        if key in clean_goal:
            return tip
    return (
        "Fuel your workouts with a balanced diet of clean proteins, complex carbohydrates, and essential fats. "
        "Drink plenty of water and prioritize high-quality sleep for recovery."
    )
