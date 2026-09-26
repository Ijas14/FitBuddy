"""Unit tests for the nutrition domain reference module."""

import pytest

from app.nutrition import (
    FLEXIBILITY,
    GENERAL,
    GENERAL_FITNESS,
    MUSCLE_GAIN,
    NUTRITION_FOCUS,
    WEIGHT_LOSS,
    classify_goal,
    nutrition_focus,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("muscle gain", MUSCLE_GAIN),
        ("Build Muscle", MUSCLE_GAIN),
        ("weight loss and fat loss", WEIGHT_LOSS),
        ("  WEIGHT LOSS  ", WEIGHT_LOSS),
        ("flexibility", FLEXIBILITY),
        ("general fitness", GENERAL_FITNESS),
        ("endurance", GENERAL_FITNESS),
        ("something unrecognisable", GENERAL),
        ("", GENERAL),
    ],
)
def test_classify_goal(text, expected):
    assert classify_goal(text) == expected


def test_classify_goal_is_case_and_whitespace_insensitive():
    assert classify_goal("  MuScLe GaIn  ") == classify_goal("muscle gain")


def test_nutrition_focus_defined_for_every_canonical_goal():
    for goal in (WEIGHT_LOSS, MUSCLE_GAIN, GENERAL_FITNESS, FLEXIBILITY, GENERAL):
        assert NUTRITION_FOCUS[goal]
        assert nutrition_focus(goal) == NUTRITION_FOCUS[goal]


def test_nutrition_focus_differs_by_goal():
    assert nutrition_focus(WEIGHT_LOSS) != nutrition_focus(MUSCLE_GAIN)


def test_nutrition_focus_falls_back_for_unknown_goal():
    assert nutrition_focus("interpretive dance") == NUTRITION_FOCUS[GENERAL]
