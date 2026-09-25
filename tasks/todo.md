# FitBuddy Task Breakdown & Execution Checklist

- [x] Task 1: Environment Setup & Project Scaffolding
  - Acceptance: Virtual environment `.venv` created, dependencies installed from `requirements.txt`, directory structure created (`app/`, `templates/`, `static/images/`, `tests/`).
  - Verify: `python3 -c "import fastapi, sqlalchemy, google.generativeai; print('OK')"` exits 0.
  - Files: `requirements.txt`, `.env.example`, `.env`, `static/images/gym-bg.jpg`.

- [x] Task 2: Database Layer & Data Models
  - Acceptance: SQLAlchemy ORM models (`User`, `WorkoutPlan`) and CRUD helper functions (`save_user`, `save_plan`, `update_plan`, `get_original_plan`, `get_user`, `get_all_users`, `delete_user`) implemented with SQLite persistence.
  - Verify: Unit test in `tests/test_database.py` passes all CRUD tests.
  - Files: `app/database.py`, `tests/test_database.py`.

- [x] Task 3: Pydantic Validation Schemas
  - Acceptance: Request/response schemas (`UserInput`, `WorkoutRequest`, `FeedbackRequest`, `WorkoutResponse`, `NutritionResponse`) defined and validated.
  - Verify: Schema validation tests in `tests/test_database.py` or `tests/test_schemas.py` pass.
  - Files: `app/schemas.py`.

- [x] Task 4: AI Generation Modules with Fallback Resilience
  - Acceptance: `gemini_generator.py` (Pro workout), `gemini_flash_generator.py` (Flash nutrition), `updated_plan.py` (Pro feedback update), and `nutrition.py` implemented with Gemini API calls and deterministic offline fallback.
  - Verify: `tests/test_ai_generators.py` tests pass both with and without API key.
  - Files: `app/gemini_generator.py`, `app/gemini_flash_generator.py`, `app/updated_plan.py`, `app/nutrition.py`, `tests/test_ai_generators.py`.

- [x] Task 5: Core Application Routes & Web Server
  - Acceptance: `app/routes.py` and `app/main.py` implement all HTML routes (`/`, `/generate-workout`, `/submit-feedback`, `/view-all-users`, `/delete-user/{user_id}`) and JSON API endpoints (`/generate-workout/gemini`, `/nutrition-tip`, `/generate-plan`, `/update-plan/{user_id}`).
  - Verify: `tests/test_web_routes.py` and `tests/test_api_routes.py` pass with 100% endpoint coverage.
  - Files: `app/main.py`, `app/routes.py`, `tests/test_web_routes.py`, `tests/test_api_routes.py`.

- [x] Task 6: Frontend Templates & Gym-Themed Styling
  - Acceptance: `index.html`, `result.html`, `all_users.html` created with responsive gym-themed dark styling, Roboto typography, structured `<pre>` blocks, feedback form, and confirmation alert.
  - Verify: Visual inspection and template rendering test via TestClient.
  - Files: `templates/index.html`, `templates/result.html`, `templates/all_users.html`, `static/css/style.css`.

- [ ] Task 7: End-to-End Verification & Browser Testing
  - Acceptance: Full user journey tested in a live browser (home form submission -> result view -> feedback revision -> all users dashboard).
  - Verify: Playwright browser test navigates, fills form, clicks buttons, and verifies DOM elements.
  - Files: `tests/test_e2e_browser.py`.
