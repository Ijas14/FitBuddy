# FitBuddy – AI Fitness Plan Generator using Gemini Models

A full-stack AI-powered fitness web application that generates personalized **7-day workout plans** and **nutrition/recovery tips** using Google's Gemini models (Gemini 1.5 Pro & Gemini Flash).

Built with **FastAPI + SQLAlchemy (SQLite) + Jinja2**.

---

## Features

| Scenario | Description |
|---|---|
| **1. Plan Generation** | Enter Name, User ID, Age, Weight, Fitness Goal, and Intensity → Gemini 1.5 Pro generates a structured 7-day plan (warm-up / main workout / cooldown) while Gemini Flash delivers a goal-aligned nutrition tip. |
| **2. Feedback-Driven Refinement** | Submit feedback (e.g. *"add more cardio"*, *"include yoga on rest days"*) → Gemini 1.5 Pro revises the plan, which is persisted separately from the original. |
| **3. Nutrition / Recovery Tips** | Standalone micro-endpoint powered by Gemini Flash for fast dietary and recovery guidance. |
| **4. Admin Dashboard** | `/view-all-users` displays every registered user with their metrics, **original** plan, and **updated** plan in a structured table, plus per-user deletion. |

---

## Project Structure

```
FitBuddy/
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
│   ├── css/style.css             # Responsive dark gym-themed styling
│   └── images/gym-bg.jpg         # Background asset
├── tests/                        # Pytest suite (unit + API + web integration)
├── tasks/                        # plan.md and todo.md tracking
├── PLAN.md                       # Full specification & architecture document
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Quick Start

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

> **Note:** The app works **without** an API key — a deterministic offline fallback generates realistic plans, tips, and revisions so the UI, API, and test suite always function.

### 4. Run the server

```bash
python -m uvicorn app.main:app --reload
```

Then open:

- Application → <http://127.0.0.1:8000>
- Interactive API docs → <http://127.0.0.1:8000/docs>

---

## Running Tests

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

The suite covers database CRUD, Pydantic validation, AI generators/fallback, HTML form routes, and JSON API contracts.

---

## API Reference

### Web (HTML / Jinja2)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Homepage input form |
| `POST` | `/generate-workout` | Generate plan, save user + plan, render `result.html` |
| `POST` | `/submit-feedback` | Revise plan from feedback, render updated `result.html` |
| `GET` | `/view-all-users` | Admin dashboard |
| `POST` | `/delete-user/{user_id}` | Delete user and associated plan (303 → dashboard) |

### JSON REST API

| Method | Path | Request Body / Query | Response |
|---|---|---|---|
| `POST` | `/generate-workout/gemini` | `{"goal": str, "intensity": str}` | `{"model": "gemini-pro", "workout_plan": str}` |
| `GET` | `/nutrition-tip` | `?goal=...` | `{"goal": str, "nutrition_tip": str}` |
| `POST` | `/generate-plan` | `UserInput` | `{"message": str, "workout_plan": str}` |
| `POST` | `/update-plan/{user_id}` | `{"feedback": str}` | `{"updated_plan": str}` |
| `GET` | `/api/users` | — | `[UserResponse, ...]` |

Example:

```bash
curl -X POST http://127.0.0.1:8000/generate-workout/gemini \
  -H 'Content-Type: application/json' \
  -d '{"goal": "weight loss", "intensity": "high"}'
```

---

## Data Model

**`users`**

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key (user-supplied ID) |
| `name` | String(100) | User's name |
| `age` | Integer | Years |
| `weight` | Float | Kilograms |
| `goal` | String(100) | Fitness goal |
| `intensity` | String(50) | Low / Medium / High |
| `schedule` | Integer | Default `7` |

**`workout_plans`**

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Auto-increment primary key |
| `user_id` | Integer | FK → `users.id` (unique, cascade delete) |
| `original_plan` | Text | Initial Gemini 1.5 Pro plan |
| `updated_plan` | Text | Feedback-revised plan (nullable) |

---

## Tech Stack

- **Backend:** FastAPI, Uvicorn
- **AI:** `google-generativeai` — Gemini 1.5 Pro (plans/updates), Gemini 1.5 Flash (tips)
- **Database:** SQLite via SQLAlchemy ORM
- **Frontend:** Jinja2, HTML5, CSS3 (Roboto, responsive dark theme)
- **Validation:** Pydantic v2
- **Testing:** Pytest, HTTPX TestClient, Playwright

---

## Documentation

- [`PLAN.md`](PLAN.md) — full specification & architecture
- [`tasks/plan.md`](tasks/plan.md) — phased implementation plan
- [`tasks/todo.md`](tasks/todo.md) — task checklist and verification status
