# FitBuddy – AI Fitness Plan Generator using Gemini Models

FitBuddy is a FastAPI web app that turns a user's profile into a 7-day workout plan and a matching
nutrition tip. Workout plans and feedback revisions come from Gemini Pro, nutrition tips from Gemini
Flash. When a user submits feedback on a stored plan, the revision is saved next to the original, and
an admin dashboard lists every user with both versions.

The stack is FastAPI, SQLAlchemy with SQLite, and Jinja2 templates.

FitBuddy is the product name used in the UI, the API title, and the documentation headings.

## Error handling

The design DOCX shows plain Gemini calls and specifies no fallback, so there is none. When a Gemini
call fails, the generator raises `GeminiError` and the app reports the exact upstream reason.

- HTML routes render a styled error page with the reason verbatim: quota exhaustion with metric and
  limit, an invalid key, an unknown model name, a network failure, or an empty or blocked response.
- JSON API endpoints answer `502 Bad Gateway` with the reason in the `detail` field.
- A failed plan generation saves nothing, so the database never holds a half-registered user. A
  failed revision leaves the stored original plan unchanged.
- If the plan succeeds but the nutrition tip fails, the result page still shows the plan with an
  inline error box explaining why the tip is missing.

## Features

| Scenario | What it does |
|---|---|
| 1. Plan generation | You enter name, user ID, age, weight, fitness goal and intensity. Gemini Pro returns a 7-day plan where each day has a warm-up, a main workout and a cooldown. Gemini Flash returns a nutrition tip matched to the goal. |
| 2. Feedback-driven refinement | You submit feedback such as "add more cardio" or "include yoga on rest days". Gemini Pro revises the plan, and the revision is stored separately from the original. |
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
│   ├── gemini_generator.py       # Gemini Pro – 7-day workout generation, GeminiError
│   ├── gemini_flash_generator.py # Gemini Flash – nutrition tips
│   ├── updated_plan.py           # Gemini Pro – feedback-based plan revision
│   └── nutrition.py              # Goal classification + per-goal nutrition focus
├── templates/
│   ├── index.html                # User input form
│   ├── result.html               # Plan, nutrition tip, feedback form, error state
│   └── all_users.html            # Admin dashboard
├── static/images/gym-bg.jpg      # Gym photo used as the page backdrop
├── fitbuddy.db                   # SQLite database, created on first run
└── requirements.txt
```

The file set follows the project structure given in the design specification. CSS is inlined into
each template, as the specification describes, and the error page is rendered by `result.html`.

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

There is no `.env.example` in the repository, so create the file yourself:

```bash
touch .env
```

```
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_PRO_MODEL=gemini-3.1-pro-preview
GEMINI_FLASH_MODEL=gemini-3.5-flash
DATABASE_URL=sqlite:///./fitbuddy.db
```

The app will not serve AI content without a key. Generation attempts return an error page (HTML) or
a `502` with the reason (API) saying the key is missing.

### Model names

The specification names `gemini-1.5-pro` and `gemini-1.5-flash`. Google has retired both, and they
now return 404, which surfaces as the same error page or API `502` as any other failure. The
defaults above are current names that keep the specified split of Pro for workout plans and Flash
for nutrition tips.

Free-tier keys have no Pro quota, so `gemini-3.1-pro-preview` answers with 429 and plan generation
fails until billing is enabled on the project. The Flash free tier allows 20 requests per day; once
those are used up, nutrition tips fail the same way until the daily reset. The error page shows the
status code, quota metric and retry hint for each case.

### 4. Run the server

```bash
python -m uvicorn app.main:app --reload
```

Then open:

- Application: <http://127.0.0.1:8000>
- Interactive API docs: <http://127.0.0.1:8000/docs>

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

`POST /generate-workout/gemini`, `GET /nutrition-tip` and `POST /generate-plan` answer `502 Bad
Gateway` with the exact Gemini failure reason in `detail` when the model call fails.
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
| `original_plan` | Text | Initial Gemini Pro plan |
| `updated_plan` | Text | Feedback-revised plan, nullable |

## Tech stack

- Backend: FastAPI, Uvicorn
- AI: `google-generativeai`. Gemini Pro for plans and updates, Gemini Flash for tips
- Database: SQLite through the SQLAlchemy ORM
- Frontend: Jinja2, HTML5, CSS3. Roboto, with the gym photo as the page backdrop
- Validation: Pydantic v2

`google-generativeai` is end-of-life and prints a warning on import. Migrating to `google-genai` is
outstanding.

## Credits

`static/images/gym-bg.jpg` is a gym photograph from Unsplash
(`images.unsplash.com/photo-1571019613454-1cb2f99b2d8b`), used under the
[Unsplash License](https://unsplash.com/license). It is the same photograph the source specification
DOCX uses in its screenshots.
