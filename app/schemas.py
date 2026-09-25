from typing import Optional
from pydantic import BaseModel, Field


class UserInput(BaseModel):
    user_id: int = Field(..., description="Unique ID for the user")
    username: str = Field(..., min_length=1, max_length=100, description="Name of the user")
    age: int = Field(..., gt=0, lt=130, description="Age in years")
    weight: float = Field(..., gt=0.0, description="Weight in kg")
    goal: str = Field(..., min_length=1, max_length=100, description="Fitness goal")
    intensity: str = Field(..., min_length=1, max_length=50, description="Preferred workout intensity")


class WorkoutRequest(BaseModel):
    goal: str = Field(..., min_length=1, description="Fitness goal")
    intensity: str = Field(..., min_length=1, description="Preferred intensity")


class FeedbackRequest(BaseModel):
    feedback: str = Field(..., min_length=1, description="Feedback message to update the plan")


class WorkoutResponse(BaseModel):
    model: str
    workout_plan: str


class NutritionResponse(BaseModel):
    goal: str
    nutrition_tip: str


class PlanGenerationResponse(BaseModel):
    message: str
    workout_plan: str


class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    weight: float
    goal: str
    intensity: str
    original_plan: Optional[str] = "N/A"
    updated_plan: Optional[str] = "Not updated"
