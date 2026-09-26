# FitBuddy implementation plan

## Phase 1: environment and scaffolding

- Create `.venv` with Python 3.12.
- Write `requirements.txt` with pinned ranges: `fastapi`, `uvicorn[standard]`, `jinja2`, `sqlalchemy`,
  `python-multipart`, `google-generativeai`, `pydantic`, `python-dotenv`, `pytest`, `httpx`,
  `playwright`.
- Create `app/`, `templates/`, `static/images/`, `static/css/`, `tests/` and `tasks/`.
- Add `.env.example` and `.env`.
- Add the gym background at `static/images/gym-bg.jpg`.

## Phase 2: database layer

- Set up SQLite and SQLAlchemy in `app/database.py`.
- Define the `User` and `WorkoutPlan` models.
- Implement the helpers: `save_user`, `save_plan`, `update_plan`, `get_original_plan`, `get_user`,
  `get_all_users`, `get_all_plans`, `delete_user`.
- Cover CRUD with unit tests in `tests/test_database.py`.

## Phase 3: validation schemas

- Implement `UserInput`, `WorkoutRequest`, `FeedbackRequest`, `WorkoutResponse`, `NutritionResponse`
  and `PlanGenerationResponse` in `app/schemas.py`.
- Write unit tests for validation.

## Phase 4: AI generators and fallback

- `app/gemini_generator.py` calls Gemini 1.5 Pro for the 7-day plan.
- `app/gemini_flash_generator.py` calls Gemini Flash for the nutrition tip.
- `app/updated_plan.py` revises a plan from feedback.
- `app/nutrition.py` holds the goal-keyed guidance text.
- Each module needs a deterministic local fallback so the app runs with no key and the tests are
  reproducible.
- `tests/test_ai_generators.py` covers both the live path and the fallback.

## Phase 5: routing and application core

- `app/main.py` configures FastAPI, mounts static files, loads templates and initialises the database.
- `app/routes.py` holds the form handlers (`/`, `/generate-workout`, `/submit-feedback`,
  `/view-all-users`, `/delete-user/{user_id}`) and the JSON endpoints (`/generate-workout/gemini`,
  `/nutrition-tip`, `/generate-plan`, `/update-plan/{user_id}`).
- Integration tests go in `tests/test_web_routes.py` and `tests/test_api_routes.py`.

## Phase 6: templates and styling

- `templates/index.html` holds the input form over the gym background.
- `templates/result.html` shows the user summary, the plan in a `<pre>` block, the nutrition tip, the
  feedback form and the update confirmation.
- `templates/all_users.html` holds the admin table, the plan columns and the delete action.
- `static/css/style.css` implements the gym-photo layout, blue accents and Roboto. Colour values come
  from sampling the DOCX screenshots; see `PLAN.md` section 8.1.

## Phase 7: runtime and browser testing

- Start Uvicorn on port 8000.
- Run the Playwright journey: submit the home form, check the plan and tip on the result page, submit
  feedback and confirm the revision and the message, then open `/view-all-users` and confirm the row.
- Remove the test records afterwards.
- Run the full suite and finish the documentation.
