# FitBuddy – AI Fitness Plan Generator using Gemini Models

Specification and architecture for the implementation.

The source of truth for the interface is the project DOCX, including the 28 screenshots embedded in
it. `PLAN.md` is a derived document: where the two disagree, the DOCX wins. Section 8 records the
measured values and how they were obtained.

## 1. Objective

FitBuddy generates 7-day workout plans and nutrition or recovery advice from a user's demographic and
fitness profile. Feedback revises a stored plan, and an admin dashboard shows every user alongside
their plan history.

Four scenarios drive the design:

- **Plan generation.** The user submits name, user ID, age, weight in kilograms, fitness goal and
  preferred intensity (Low, Medium or High). Gemini 1.5 Pro returns a day-by-day regimen, and Gemini
  Flash returns advice matched to the goal. Both the profile and the plan are written to SQLite.
- **Feedback-driven refinement.** The user submits their user ID plus a request such as "add more
  cardio" or "include yoga on rest days". Gemini 1.5 Pro reads the original plan and the request and
  returns a revision, leaving days that need no change alone. The revision is stored and a
  confirmation is shown.
- **Standalone nutrition and recovery endpoint.** A small Gemini Flash endpoint that returns a single
  practical tip.
- **Coach or admin dashboard.** `/view-all-users` lists registered users with their metrics, the
  original plan and the updated plan in one table, with per-user deletion.

## 2. Architecture and tech stack

```
User (Browser / API Client)
         │
         ▼
 FastAPI Backend (app/main.py, app/routes.py)
 ┌────────────────────────────────────────────────────────┐
 │ - Static Asset Serving (/static)                       │
 │ - Jinja2 Template Engine (/templates)                  │
 │ - Form & JSON Request Parsing (app/schemas.py)         │
 └───────────────────┬────────────────────────────────────┘
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
 AI Layer                     Database Layer (app/database.py)
 - Gemini 1.5 Pro             - SQLite (fitbuddy.db)
   (Workout Gen & Update)     - SQLAlchemy ORM
 - Gemini Flash               - Tables: users, workout_plans
   (Nutrition Tips)
 - Error surfaces (exact Gemini failure reasons)
```

| Layer | Choice |
|---|---|
| Language | Python 3.12+ |
| Web framework | FastAPI |
| Server | Uvicorn (ASGI) |
| AI SDK | `google-generativeai` |
| Database | SQLite through the SQLAlchemy ORM |
| Templating | Jinja2 with HTML5 and CSS3 |
| Validation | Pydantic v2 |
| Testing | Pytest, HTTPX via `fastapi.testclient`, Playwright |

Model assignment:

- Gemini 1.5 Pro drives `generate_workout_gemini` (workout plans) and `update_workout_plan` (feedback
  revisions).
- Gemini Flash drives `generate_nutrition_tip_with_flash` (nutrition tips).
- Each generator raises `GeminiError` with the exact reason when `GOOGLE_API_KEY` is missing or the
  API call fails; see §6.4.

## 3. Directory structure

```
fitbuddy-ai/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point, mounts, lifespan
│   ├── routes.py                # Web form handlers and JSON REST API routes
│   ├── database.py              # SQLAlchemy DB models, session management, CRUD
│   ├── schemas.py               # Pydantic models for validation and serialization
│   ├── gemini_generator.py      # Gemini 1.5 Pro 7-day workout plan generator
│   ├── gemini_flash_generator.py# Gemini Flash nutrition tip generator
│   ├── gemini_error.py          # GeminiError + exact-reason extraction
│   └── updated_plan.py          # Gemini 1.5 Pro feedback-based plan refinement
├── templates/
│   ├── index.html               # Homepage & user input form
│   ├── result.html              # Plan display, nutrition tip & feedback form
│   └── all_users.html           # Admin dashboard of users and plans
├── static/
│   ├── images/
│   │   └── gym-bg.jpg           # Gym-themed hero/background image
│   └── css/
│       └── style.css            # Gym-photo layout, light theme
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures (isolated SQLite DB, stripped API key)
│   ├── test_database.py         # Unit tests for CRUD and ORM models
│   ├── test_ai_generators.py    # Unit tests for Gemini calls & error reasons
│   ├── test_web_routes.py       # Integration tests for HTML endpoints
│   ├── test_api_routes.py       # Integration tests for JSON API endpoints
│   └── test_e2e_browser.py      # Playwright journey against a live server
├── tasks/
│   ├── plan.md                  # Implementation phase plan
│   └── todo.md                  # Task-by-task execution checklist and verification log
├── .env.example                 # Template for GOOGLE_API_KEY & settings
├── requirements.txt             # Locked project dependencies
├── PLAN.md                      # This specification & architecture document
└── FitBuddy – AI Fitness Plan Generator using Gemini Models.docx
```

## 4. Data models and database design

### 4.1 ORM models (`app/database.py`)

Table `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary key | Explicit user ID supplied by the user |
| `name` | String(100) | Not null | User full name |
| `age` | Integer | Not null | Age in years |
| `weight` | Float | Not null | Weight in kilograms |
| `goal` | String(100) | Not null | Fitness goal, e.g. weight loss or muscle gain |
| `intensity` | String(50) | Not null | Low, Medium or High |
| `schedule` | Integer | Default 7 | Plan length in days |

Table `workout_plans`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary key, auto-increment | Internal plan ID |
| `user_id` | Integer | Foreign key to `users.id`, unique, indexed | Reference to user |
| `original_plan` | Text | Nullable | Initial Gemini 1.5 Pro plan |
| `updated_plan` | Text | Nullable, default none | Feedback-revised plan |

### 4.2 Database helper functions

- `save_user(user_id: int, name: str, age: int, weight: float, goal: str, intensity: str) -> User`:
  upserts the user, creating or updating as needed.
- `save_plan(user_id: int, plan: str) -> WorkoutPlan`: stores or replaces the original plan.
- `update_plan(user_id: int, updated_text: str) -> WorkoutPlan`: persists a revision.
- `get_original_plan(user_id: int) -> Optional[str]`: returns the original plan text.
- `get_user(user_id: int) -> Optional[User]`: returns one user.
- `get_all_users() -> List[User]`: returns every user.
- `get_all_plans() -> List[WorkoutPlan]`: returns every plan.
- `delete_user(user_id: int) -> bool`: removes a user and their plans, used by the admin delete.

## 5. Pydantic schemas (`app/schemas.py`)

- `UserInput`: `user_id: int`, `username: str`, `age: int` (gt 0, lt 130), `weight: float` (gt 0.0),
  `goal: str`, `intensity: str`
- `WorkoutRequest`: `goal: str`, `intensity: str`
- `FeedbackRequest`: `feedback: str`
- `WorkoutResponse`: `model: str`, `workout_plan: str`
- `NutritionResponse`: `goal: str`, `nutrition_tip: str`
- `PlanGenerationResponse`: `message: str`, `workout_plan: str`
- `UserResponse`: `id`, `name`, `age`, `weight`, `goal`, `intensity`, `original_plan`, `updated_plan`

## 6. AI prompts and failure behaviour

### 6.1 Gemini 1.5 Pro: 7-day workout generation (`app/gemini_generator.py`)

```text
You are a professional fitness trainer.

Create a personalized, structured 7-day workout plan for someone with the goal of **{goal}**, and prefers **{intensity} intensity** workouts.

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
```

### 6.2 Gemini Flash: nutrition tip (`app/gemini_flash_generator.py`)

```text
Give one clear, helpful nutrition or recovery tip for someone focused on '{goal}'.
The tip should be practical, friendly, and easy to understand.
```

### 6.3 Gemini 1.5 Pro: feedback refinement (`app/updated_plan.py`)

```text
You are a professional fitness trainer assistant.

Here's the original 7-day workout plan:
{original_plan}

User Feedback:
"{user_feedback}"

Based on the feedback, revise the relevant parts of the workout plan. Keep the format and rest of the plan unchanged if not needed.
```

### 6.4 Failure behaviour (no offline fallback)

The DOCX specifies no fallback, so there is none. When `GOOGLE_API_KEY` is absent, invalid, or the
call fails, each generator raises `app.gemini_error.GeminiError` whose message carries the exact
reason — quota exhaustion with the quota metric and retry hint, an unknown model name, an invalid
key, a network failure, or an empty/blocked response. Nothing is written to the database when plan
generation fails, and a failed revision leaves the stored original plan untouched. HTML routes
render `templates/error.html` with the reason verbatim; JSON API endpoints answer `502` with the
reason in `detail`. The exception to the 502 rule is the DOCX-specified `POST /update-plan/{user_id}`
missing-plan contract: HTTP 200 with an `error` key.

## 7. Routes and interfaces (`app/routes.py`)

### 7.1 Web interface routes (Jinja2 HTML)

1. `GET /` renders `index.html` with the workout generator form.
2. `POST /generate-workout` accepts `username`, `user_id`, `age`, `weight`, `goal` and `intensity`
   as form data. It calls `generate_workout_gemini(...)` first — on `GeminiError` it renders
   `error.html` with the exact reason and persists nothing — then
   `generate_nutrition_tip_with_flash(...)` (a tip failure becomes an inline warning on the result
   page while the plan still renders), then `save_user(...)` and `save_plan(...)`, and returns
   `result.html` carrying the user details, the plan in a `<pre>` block and the nutrition tip.
3. `POST /submit-feedback` accepts `user_id` and `feedback`. It reads the original plan with
   `get_original_plan(user_id)`, calls `update_workout_plan(original_plan, feedback)`, saves with
   `update_plan(user_id, updated_plan)`, and re-renders `result.html` with the user info, the revised
   plan, the nutrition tip and the message "Your plan has been updated based on your feedback!".
   An unknown user or a missing original plan renders `error.html` with status 404 (this replaces
   the bare JSON the framework would otherwise emit); a revision failure renders `error.html` with
   the exact reason and leaves the stored plan unchanged.
4. `GET /view-all-users` reads users and plans and renders `all_users.html` with columns for user
   ID, name, age, weight, goal and intensity, followed by the original and updated plans in `<pre>`
   blocks and a delete action.
5. `POST /delete-user/{user_id}` removes the user and their plans, then redirects to
   `/view-all-users`.

### 7.2 REST API endpoints (JSON)

1. `POST /generate-workout/gemini` takes a `WorkoutRequest` and returns
   `{"model": "gemini-pro", "workout_plan": str}`.
2. `GET /nutrition-tip` takes `?goal=...` and returns `{"goal": str, "nutrition_tip": str}`.
3. `POST /generate-plan` takes a `UserInput`, creates the user and plan, and returns
   `{"message": str, "workout_plan": str}`.
4. `POST /update-plan/{user_id}` takes a `FeedbackRequest`, updates the plan and returns
   `{"updated_plan": str}`. When no plan exists it returns HTTP 200 with
   `{"error": "Original plan not found for this user."}`. The DOCX's own code screenshot shows a bare
   `return` there, which makes 200 the specified behaviour; do not "fix" it to 404.
5. `GET /api/users` returns every user object with its plans.

## 8. Frontend specification

### 8.1 Design system

The values below were sampled from pixels in the DOCX screenshots (`word/media/image*.png`). Re-measure
rather than adjust by eye if the design is revisited.

| Property | Value |
|---|---|
| Background photo | `static/images/gym-bg.jpg` at full strength, with no white gradient overlay |
| Card | `rgba(255, 255, 255, 0.95)`, border `#e6e6e6`, radius `24px`, shadow `0 10px 30px rgba(15,32,58,.12)` |
| Primary button | `#3b82f6` |
| Table header | `#1e88e5` |
| Success text | `#0a8a3e` |
| Danger | `#dc2626` |
| Headings | `#1f2937` |
| Form labels | `#111827` |
| Body text | `#33404f` |
| Placeholder | `#757575` |
| Form control and table cell borders | `#cccccc` |
| Plan `<pre>` panel | `#f3f4f6` |
| Admin page background | `#f0f4f8` |
| Container widths | `min(860px, 100%)` home, `min(1100px, 100%)` result, `min(1500px, 100%)` admin table |

Two of these came out of measurement rather than reading the file:

- **No overlay on the photo.** Compositing `gym-bg.jpg` against the reference screenshots (both use
  `background-size: cover; background-position: center`, so the same raw pixel lands in the same place)
  and solving `out = raw·(1-a) + 255·a` gives a mean overlay alpha of about 0.00. A white wash
  desaturates the page away from the spec.
- **Card alpha and geometry.** The reference home card spans x 538 to 1363 at a 1918 px viewport, so it
  is 825 px wide. The implemented value is 836 px. The result page column is wider than the home
  column because plans need the room, which is why the two container widths differ.

Typography is Roboto from Google Fonts. The feedback `<textarea>` keeps the monospace face the
reference shows, and formatted plans render in `'Roboto Mono'` on the `#f3f4f6` panel.

The admin dashboard is a flat `#f0f4f8` page with the table sitting directly on it. The reference has
no photograph and no card wrapper on that page; a colour histogram of `image7.png` shows 1,123
distinct colours with no photographic content at all.

### 8.2 Pages

`index.html`

- Six inputs: Name, User ID, Age, Weight (kg), Fitness Goal, Workout Intensity.
- Only the Fitness Goal field has a placeholder. The other four render empty.
- Intensity defaults to `Low`.
- The submit button is full width and reads "Generate Plan".

`result.html`

- An `<h1>` of "🏋️ Your Personalized Workout Plan". The emoji is the weightlifter, which is what the
  reference shows; the home page uses the flexed biceps instead.
- A user summary card listing name, user ID, age, weight, goal and intensity as bold-label rows.
- A workout plan card with the plan in a `<pre>` block.
- A nutrition tip card of plain left-aligned prose, with no panel behind it.
- A feedback card with an empty User ID field showing its placeholder, a textarea, and a Submit
  Feedback button. The field starts empty because the reference shows it that way and the placeholder
  text tells the user to type their ID.
- A confirmation line in plain green text after a revision, with no panel behind it.
- Links to "Generate New Plan" and "View All Users".

`all_users.html`

- A centred `<h1>` of "📋 FitBuddy - All Users & Workout Plans".
- A table with nine columns: User ID, Name, Age, Weight (kg), Goal, Intensity, Original Plan, Updated
  Plan, and a delete action. The first six are centre-aligned; the two plan columns are left-aligned.
- Plans render unclipped, without a scroll box.
- A link back to the home page.

Four elements in the app do not appear in any DOCX screenshot and are deliberate additions: the
header nav bar, the footer, the "+ Register New User" button, and the subtitle under the home page
heading. Without the nav, the admin dashboard and `/docs` would only be reachable by typing a URL,
which undercuts scenario 4.

## 9. Verification and quality gates

1. **Database gate.** Pytest covers schema creation, foreign keys and the CRUD helpers.
2. **AI engine gate.** Tests exercise the prompts, the success paths with a mocked SDK call, and the
   error paths (missing key, quota failure, empty/blocked response), never the network.
3. **API and route gate.** Integration tests check status codes, HTML rendering, form submission and
   the JSON contracts.
4. **End-to-end browser gate.** A Playwright test confirms the full journey: load the home page, fill
   the form, generate a plan, check the result, submit feedback and verify the revised plan and
   confirmation, then open `/view-all-users` and confirm the record appears with both plans.

`tests/conftest.py` forces an isolated `DATABASE_URL` before importing any `app.*` module and strips
`GOOGLE_API_KEY`. Without the first, pytest teardown ran `drop_all` against the development database
and broke a running server; without the second, the suite would depend on a real key.
