import os
from typing import List, Optional
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.schemas import (
    UserInput,
    WorkoutRequest,
    FeedbackRequest,
    WorkoutResponse,
    NutritionResponse,
    PlanGenerationResponse,
    UserResponse,
)
from app.database import (
    save_user,
    save_plan,
    update_plan,
    get_original_plan,
    get_user,
    get_all_users,
    get_all_plans,
    delete_user,
)
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter()


def _user_row(user, plan) -> dict:
    """Flatten a user and their (optional) plan into a template/API friendly dict."""
    return {
        "id": user.id,
        "name": user.name,
        "age": user.age,
        "weight": user.weight,
        "goal": user.goal,
        "intensity": user.intensity,
        "original_plan": plan.original_plan if plan and plan.original_plan else "N/A",
        "updated_plan": plan.updated_plan if plan and plan.updated_plan else "Not updated",
    }


# -------------------------------------------------------------
# Web HTML Routes (Jinja2)
# -------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Displays the user input form via index.html."""
    return templates.TemplateResponse(request=request, name="index.html")


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_form(
    request: Request,
    username: str = Form(...),
    user_id: int = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
):
    """Processes user form submission, saves user & plan, and renders result.html."""
    save_user(
        user_id=user_id,
        name=username,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
    )
    workout_plan = generate_workout_gemini({"goal": goal, "intensity": intensity})
    nutrition_tip = generate_nutrition_tip_with_flash(goal)
    save_plan(user_id=user_id, plan=workout_plan)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "username": username,
            "user_id": user_id,
            "age": age,
            "weight": weight,
            "goal": goal,
            "intensity": intensity,
            "workout_plan": workout_plan,
            "nutrition_tip": nutrition_tip,
            "updated_message": None,
        },
    )


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_form(
    request: Request,
    user_id: int = Form(...),
    feedback: str = Form(...),
):
    """Revises workout plan based on user feedback and displays updated result.html."""
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    original_plan = get_original_plan(user_id)
    if not original_plan:
        raise HTTPException(status_code=404, detail="Original plan not found for this user.")

    updated_plan_text = update_workout_plan(original_plan, feedback)
    update_plan(user_id, updated_plan_text)
    nutrition_tip = generate_nutrition_tip_with_flash(user.goal)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "username": user.name,
            "user_id": user.id,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
            "workout_plan": updated_plan_text,
            "nutrition_tip": nutrition_tip,
            "updated_message": "Your plan has been updated based on your feedback!",
        },
    )


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request):
    """Admin view: Displays all registered users and their workout plans."""
    plans_by_user = {plan.user_id: plan for plan in get_all_plans()}
    user_data = [_user_row(user, plans_by_user.get(user.id)) for user in get_all_users()]

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "users": user_data,
        },
    )


@router.post("/delete-user/{user_id}")
def delete_user_route(user_id: int):
    """Admin route to delete a user and associated plans."""
    delete_user(user_id)
    return RedirectResponse(url="/view-all-users", status_code=status.HTTP_303_SEE_OTHER)


# -------------------------------------------------------------
# REST API Endpoints (JSON)
# -------------------------------------------------------------

@router.post("/generate-workout/gemini", response_model=WorkoutResponse)
def generate_gemini_workout(request: WorkoutRequest):
    """1. API: Generate workout using Gemini Pro."""
    try:
        result = generate_workout_gemini(
            {
                "goal": request.goal,
                "intensity": request.intensity,
            }
        )
        return WorkoutResponse(model="gemini-pro", workout_plan=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nutrition-tip", response_model=NutritionResponse)
def get_flash_tip(goal: str):
    """2. API: Generate nutrition tip using Gemini Flash."""
    try:
        tip = generate_nutrition_tip_with_flash(goal)
        return NutritionResponse(goal=goal, nutrition_tip=tip)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-plan", response_model=PlanGenerationResponse)
def generate_plan(user_data: UserInput):
    """3. API: Save user info & generate plan."""
    try:
        save_user(
            user_id=user_data.user_id,
            name=user_data.username,
            age=user_data.age,
            weight=user_data.weight,
            goal=user_data.goal,
            intensity=user_data.intensity,
        )
        plan = generate_workout_gemini(
            {
                "goal": user_data.goal,
                "intensity": user_data.intensity,
            }
        )
        save_plan(user_data.user_id, plan)
        return PlanGenerationResponse(
            message="Workout plan generated and saved successfully!",
            workout_plan=plan,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")


@router.post("/update-plan/{user_id}", response_model=dict)
def update_user_plan(user_id: int, data: FeedbackRequest):
    """4. API: Update workout plan based on user feedback."""
    original = get_original_plan(user_id)
    if not original:
        return {"error": "Original plan not found for this user."}
    updated = update_workout_plan(original, data.feedback)
    update_plan(user_id, updated)
    return {"updated_plan": updated}


@router.get("/api/users", response_model=List[UserResponse])
def get_api_users():
    """5. API: Fetch all users and plans as JSON."""
    plans_by_user = {plan.user_id: plan for plan in get_all_plans()}
    return [
        UserResponse(**_user_row(user, plans_by_user.get(user.id)))
        for user in get_all_users()
    ]
