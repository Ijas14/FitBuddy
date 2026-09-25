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

- [x] Task 7: End-to-End Verification & Browser Testing
  - Acceptance: Full user journey tested in a live browser (home form submission -> result view -> feedback revision -> all users dashboard).
  - Verify: Playwright browser test navigates, fills form, clicks buttons, and verifies DOM elements.
  - Files: `tests/test_e2e_browser.py`.

---

## Verification Log

**Final test suite:** `26 passed` — `PYTHONPATH=. python -m pytest tests/ -v`

| Test module | Tests | Covers |
|---|---|---|
| `test_database.py` | 6 | ORM models, CRUD helpers, cascade delete |
| `test_schemas.py` | 5 | Pydantic validation (valid + invalid payloads) |
| `test_ai_generators.py` | 4 | Gemini prompts + deterministic offline fallback |
| `test_api_routes.py` | 5 | All JSON REST API contracts |
| `test_web_routes.py` | 5 | All HTML form routes + template rendering |
| `test_e2e_browser.py` | 1 | Full browser journey (Playwright) |

**Live server:** `python -m uvicorn app.main:app --port 8010` → started cleanly, **0 console errors**.

**Browser E2E journey (Playwright, validated against DOCX screenshots):**

| Step | Result |
|---|---|
| `GET /` renders input form (Name, User ID, Age, Weight, Goal, Intensity) | ✅ matches DOCX Image 24 |
| Submit form → `POST /generate-workout` | ✅ 200, `result.html` rendered |
| User Information card shows name/id/age/weight/goal/intensity | ✅ matches DOCX Image 25 |
| Workout Plan renders Day 1–7 with Warm-up / Main Workout / Cooldown | ✅ matches DOCX Images 16 & 23 |
| Nutrition Tip card renders goal-aligned advice | ✅ matches DOCX Image 14 |
| Feedback form → `POST /submit-feedback` | ✅ 200, updated plan persisted |
| Confirmation banner text | ✅ `Your plan has been updated based on your feedback!` (DOCX Image 22) |
| `GET /view-all-users` admin table | ✅ 9 columns incl. `<pre>` Original + Updated plans (DOCX Images 7 & 19) |
| `POST /delete-user/{id}` | ✅ 303 → dashboard, cascade delete verified |
| `GET /docs` | ✅ 200 |

**REST API contract checks (curl):** `/generate-workout/gemini`, `/nutrition-tip`, `/generate-plan`, `/update-plan/{id}` (incl. error body), `/api/users` — all return documented shapes.

**Responsive & accessibility checks (Playwright):**

| Check | Result |
|---|---|
| No horizontal overflow at 375px (mobile) | ✅ `scrollWidth == 375` |
| Every form control has an associated `<label>` | ✅ 100% |
| Exactly one page-level `<h1>` per page | ✅ fixed during review |
| `lang="en"` + descriptive `<title>` | ✅ |
| Images have `alt` attributes | ✅ |
| Console errors/warnings | ✅ 0 |

### Defects found and fixed during verification

1. **Test suite corrupted the live dev database** — pytest teardown ran `drop_all` against the shared `fitbuddy.db`, breaking a concurrently running Uvicorn server (`no such table: users`, surfaced as `Internal Server Error` in the browser).
   → Fixed by `tests/conftest.py`, which forces an isolated `DATABASE_URL` (temp file) *before* any `app.*` module is imported, plus a session-scoped cleanup fixture. Verified: dev DB survives a full test run with its schema intact.

2. **Accessibility gap — no `<h1>`** on any page.
   → Added a single page-level `<h1>` per template (`Generate Your Personalized 7-Day Fitness Plan`, `Your Personalized Workout Plan`, `All Users & Workout Plans`) with matching CSS, keeping `<h2>` for card headings.

3. **E2E navigation assertions were flaky** (`wait_for_load_state` raced the commit, and `to_have_url` treated the string as a literal).
   → Replaced with `page.expect_navigation()` context managers and `expect(page).to_have_url(re.compile(...))`. Verified stable across repeated full-suite runs.

4. **Admin table title mismatch** — test caught that the rendered title used an en dash (`–`) instead of the hyphen (`-`) shown in the DOCX screenshot. Realigned to `FitBuddy - All Users & Workout Plans`.

5. **Mobile result-page horizontal overflow** (Playwright MCP, 375px: `scrollWidth 440` vs viewport 375, caused by the `.btn-secondary` "View All Users" link) and **fixed container widths** that did not scale with screen size.
   → Fixed in `static/css/style.css`: fluid `clamp()` spacing/padding, container widths `min(1200px, 100%)` / `min(1600px, 100%)` with a 1400px+ tier, wrapping header nav, wrapping `.action-group` buttons that stack full-width under 640px, and a fluid `.page-header` on the admin dashboard. Verified 0 page-level overflow at 320/375/480/640/768/900/1024/1280/1440/1600/1920px on `/` and `/view-all-users`, and the full generate-plan journey at 320/375/768/1440px.

