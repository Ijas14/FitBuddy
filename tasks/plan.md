# FitBuddy Implementation Plan

## Phase 1: Environment Setup & Project Scaffolding
- Setup virtual environment `.venv` with Python 3.12.
- Define `requirements.txt` with locked dependencies: `fastapi`, `uvicorn[standard]`, `jinja2`, `sqlalchemy`, `python-multipart`, `google-generativeai`, `pydantic`, `python-dotenv`, `pytest`, `httpx`.
- Create folders: `app/`, `templates/`, `static/images/`, `static/css/`, `tests/`, `tasks/`.
- Setup `.env.example` and `.env`.
- Copy gym background asset to `static/images/gym-bg.jpg`.

## Phase 2: Database Layer & Data Models
- Implement SQLite + SQLAlchemy in `app/database.py`.
- Define `User` and `WorkoutPlan` models.
- Implement helper functions: `save_user`, `save_plan`, `update_plan`, `get_original_plan`, `get_user`, `get_all_users`, `get_all_plans`, `delete_user`.
- Write unit tests in `tests/test_database.py` and verify with Pytest.

## Phase 3: Validation Schemas
- Implement Pydantic models in `app/schemas.py`: `UserInput`, `WorkoutRequest`, `FeedbackRequest`, `WorkoutResponse`, `NutritionResponse`, `PlanGenerationResponse`.
- Write unit tests for data validation.

## Phase 4: AI Generation Modules with Resilient Fallback
- Implement `app/gemini_generator.py` for Gemini 1.5 Pro workout plan generation.
- Implement `app/gemini_flash_generator.py` for Gemini Flash nutrition tip generation.
- Implement `app/updated_plan.py` for feedback-driven plan adjustment.
- Implement `app/nutrition.py` helper module.
- Embed robust offline fallback generators for 100% test reliability and zero-key local operation.
- Write tests in `tests/test_ai_generators.py` covering both API and fallback execution.

## Phase 5: Routing & FastAPI Core Application
- Implement `app/main.py` configuring FastAPI, static mounts, template loading, and DB initialization.
- Implement `app/routes.py` with all form handlers (`/`, `/generate-workout`, `/submit-feedback`, `/view-all-users`, `/delete-user/{user_id}`) and JSON API endpoints (`/generate-workout/gemini`, `/nutrition-tip`, `/generate-plan`, `/update-plan/{user_id}`).
- Write integration tests in `tests/test_web_routes.py` and `tests/test_api_routes.py`.

## Phase 6: Jinja2 Templates & Modern Gym Aesthetic
- Build `templates/index.html` with clean form and gym background.
- Build `templates/result.html` displaying personalized summary, workout plan `<pre>`, nutrition tip banner, feedback form, and update confirmation banner.
- Build `templates/all_users.html` with admin table view, plan `<pre>` displays, and deletion actions.
- Build `static/css/style.css` with responsive dark layout, athletic orange/cyan accents, and Roboto font.

## Phase 7: Live Runtime & Browser E2E Testing
- Start local Uvicorn server on port 8000.
- Execute Playwright browser verification:
  - Fill and submit user details on `/`.
  - Validate generated workout plan and nutrition tip on `/generate-workout`.
  - Submit feedback and verify updated plan and confirmation banner.
  - Navigate to `/view-all-users` and confirm table rendering.
  - Clean up test records.
- Run complete test suite and finalize documentation.
