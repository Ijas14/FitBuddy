# FitBuddy – AI Fitness Plan Generator using Gemini Models

A FastAPI web app that builds 7-day workout plans and nutrition or recovery tips from a user's
fitness goal. Plans come from Google's Gemini models: Gemini 1.5 Pro for workout plans and
revisions, Gemini Flash for nutrition tips.

The stack is FastAPI, SQLAlchemy with SQLite, and Jinja2 templates.

The project directory is named `fitbuddy-ai`. "FitBuddy" remains the product name used in the UI,
the API title, and the documentation headings.

## Features

| Scenario | What it does |
|---|---|
| 1. Plan generation | You enter name, user ID, age, weight, fitness goal and intensity. Gemini 1.5 Pro returns a 7-day plan where each day has a warm-up, a main workout and a cooldown. Gemini Flash returns a nutrition tip matched to the goal. |
| 2. Feedback-driven refinement | You submit feedback such as "add more cardio" or "include yoga on rest days". Gemini 1.5 Pro revises the plan, and the revision is stored separately from the original. |
| 3. Nutrition and recovery tips | A standalone endpoint backed by Gemini Flash that returns one dietary or recovery suggestion. |
| 4. Admin dashboard | `/view-all-users` lists every registered user with their details, the original plan, any updated plan, and a delete button per row. |

## Project structure

```
fitbuddy-ai/
├── app/
│   ├── main.py                   # FastAPI entry point (static mount + router)
│   ├── routes.py                 # HTML form routes + JSON REST API routes
│   ├── database.py               # SQLAlchemy models & CRUD helpers
│   ├── schemas.py                # Pydantic validation models
│   ├── gemini_generator.py       # Gemini 1.5 Pro – 7-day workout generation
│   ├── gemini_flash_generator.py # Gemini Flash – nutrition tips
│   ├── updated_plan.py           # Gemini 1.5 Pro – feedback-based plan revision
│   └── nutrition.py              # Goal-based nutrition guidance helpers
├── templates/
│   ├── index.html                # User input form
│   ├── result.html               # Plan, nutrition tip & feedback form
│   └── all_users.html            # Admin dashboard
├── static/
│   ├── css/style.css             # Gym-photo layout, light theme
│   └── images/gym-bg.jpg         # Gym photo used as the page backdrop
├── tests/                        # Pytest suite (unit + API + web integration)
├── tasks/                        # plan.md and todo.md tracking
├── PLAN.md                       # Specification and architecture
├── requirements.txt
├── pytest.ini
└── .env.example
```

## Quick start

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` and set your Gemini key:

```
GOOGLE_API_KEY=your_gemini_api_key_here
```

The app runs without a key. A deterministic offline fallback stands in for the model, so a fresh clone
with no Google account still serves every page and passes the suite.

### Model names

The DOCX specifies `gemini-1.5-pro` and `gemini-1.5-flash`. Google has retired both, and they now
return 404. Because the generators swallow the error and return the local plan, a retired model name
looks identical to a working one from the outside. `.env.example` uses current names that keep the
DOCX's split of Pro for workout plans and Flash for nutrition tips.

Free-tier keys have no Pro quota, so `gemini-3.1-pro-preview` answers with 429 and workout plans still
come from the fallback until billing is enabled on the project. Nutrition tips run live on the free
tier. To see which path produced a given plan, compare it against
`gemini_generator._get_fallback_workout_plan()`.

### 4. Run the server

```bash
python -m uvicorn app.main:app --reload
```

Then open:

- Application: <http://127.0.0.1:8000>
- Interactive API docs: <http://127.0.0.1:8000/docs>

## Running tests

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

The suite covers database CRUD, Pydantic validation, the AI generators and their fallback path, the
HTML form routes, and the JSON API contracts.

`tests/test_e2e_browser.py` drives a real browser through the whole journey with Playwright. It skips
itself unless a server is already listening on port 8010:

```bash
python -m uvicorn app.main:app --port 8010 &
PYTHONPATH=. python -m pytest tests/ -q
```

## API reference

### Web (HTML / Jinja2)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Homepage input form |
| `POST` | `/generate-workout` | Generate plan, save user + plan, render `result.html` |
| `POST` | `/submit-feedback` | Revise plan from feedback, render updated `result.html` |
| `GET` | `/view-all-users` | Admin dashboard |
| `POST` | `/delete-user/{user_id}` | Delete user and associated plan (303 to dashboard) |

### JSON REST API

| Method | Path | Request body / query | Response |
|---|---|---|---|
| `POST` | `/generate-workout/gemini` | `{"goal": str, "intensity": str}` | `{"model": "gemini-pro", "workout_plan": str}` |
| `GET` | `/nutrition-tip` | `?goal=...` | `{"goal": str, "nutrition_tip": str}` |
| `POST` | `/generate-plan` | `UserInput` | `{"message": str, "workout_plan": str}` |
| `POST` | `/update-plan/{user_id}` | `{"feedback": str}` | `{"updated_plan": str}` |
| `GET` | `/api/users` | none | `[UserResponse, ...]` |

`POST /update-plan/{user_id}` answers with HTTP 200 and an `error` key when no plan exists for that
user. That status code is what the source specification calls for, so it is intentional.

Example:

```bash
curl -X POST http://127.0.0.1:8000/generate-workout/gemini \
  -H 'Content-Type: application/json' \
  -d '{"goal": "weight loss", "intensity": "high"}'
```

## Data model

`users`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key, user-supplied |
| `name` | String(100) | User's name |
| `age` | Integer | Years |
| `weight` | Float | Kilograms |
| `goal` | String(100) | Fitness goal |
| `intensity` | String(50) | Low / Medium / High |
| `schedule` | Integer | Defaults to `7` |

`workout_plans`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Auto-increment primary key |
| `user_id` | Integer | FK to `users.id`, unique, cascade delete |
| `original_plan` | Text | Initial Gemini 1.5 Pro plan |
| `updated_plan` | Text | Feedback-revised plan, nullable |

## Tech stack

- Backend: FastAPI, Uvicorn
- AI: `google-generativeai`. Gemini 1.5 Pro for plans and updates, Gemini Flash for tips
- Database: SQLite through the SQLAlchemy ORM
- Frontend: Jinja2, HTML5, CSS3. Roboto, with the gym photo as the page backdrop
- Validation: Pydantic v2
- Testing: Pytest, HTTPX TestClient, Playwright

`google-generativeai` is end-of-life and prints a warning on import. Migrating to `google-genai` is
outstanding.

## Documentation

- [`PLAN.md`](PLAN.md): specification and architecture
- [`tasks/plan.md`](tasks/plan.md): phased implementation plan
- [`tasks/todo.md`](tasks/todo.md): task checklist and verification log

## Credits

`static/images/gym-bg.jpg` is a gym photograph from Unsplash
(`images.unsplash.com/photo-1571019613454-1cb2f99b2d8b`), used under the
[Unsplash License](https://unsplash.com/license). It is the same photograph the source specification
DOCX uses in its screenshots.
