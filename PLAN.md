# FitBuddy – AI Fitness Plan Generator using Gemini Models
## Comprehensive Project Specification & Implementation Plan

---

## 1. Executive Summary & Objective

**FitBuddy** is a full-stack AI-powered health and fitness web application designed to generate personalized 7-day workout plans and tailored nutrition/recovery advice. Built with **FastAPI**, **SQLAlchemy (SQLite)**, **Google Gemini AI models (Gemini 1.5 Pro & Gemini Flash)**, and **Jinja2 templating**, FitBuddy enables users to input their demographic and fitness profile, receive custom routines, dynamically adapt their plans via feedback-driven AI regeneration, and offers administrators/trainers a centralized dashboard to track all user profiles and plan histories.

### Key Capabilities & Scenarios
- **Scenario 1 (7-Day Workout & Nutrition Generation)**: Users input Name, User ID, Age, Weight (kg), Fitness Goal (e.g., Weight Loss, Muscle Gain, Flexibility), and Preferred Workout Intensity (Low, Medium, High). Gemini 1.5 Pro generates a structured day-by-day regimen (Warm-up, Main Workout, Cooldown), while Gemini Flash generates actionable, goal-aligned nutrition/recovery advice. Both user metrics and generated plans are stored in SQLite.
- **Scenario 2 (Feedback-Driven Plan Refinement)**: Users provide their User ID and feedback (e.g., "add more cardio", "include yoga on rest days"). Gemini 1.5 Pro consumes the original plan and user feedback to regenerate a revised plan, preserving unaffected days while tailoring requested modifications. An updated plan is saved to SQLite, and an update confirmation is shown.
- **Scenario 3 (Standalone Nutrition & Recovery Microservice)**: Fast, lightweight endpoint powered by Gemini Flash that delivers practical dietary and recovery tips.
- **Scenario 4 (Coach / Admin Management Dashboard)**: Comprehensive dashboard (`/view-all-users`) displaying all registered members with their metrics, original AI plans, and updated plans in a clear table format, with admin deletion capability.

---

## 2. Technical Architecture & Tech Stack

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
 - Offline Fallback Engine
```

### Technology Matrix
- **Language**: Python 3.12+
- **Backend Framework**: FastAPI
- **Server**: Uvicorn (ASGI)
- **AI / LLM SDK**: Google Generative AI SDK (`google-generativeai`)
  - **Gemini 1.5 Pro**: Workout plan generation (`generate_workout_gemini`) and feedback-based refinement (`update_workout_plan`).
  - **Gemini Flash (1.5 Flash)**: Nutrition and recovery tips (`generate_nutrition_tip_with_flash`).
  - **Fallback / Mock Engine**: Automated graceful degradation if `GOOGLE_API_KEY` is absent or API quota/network is unavailable.
- **Database**: SQLite3 via SQLAlchemy ORM.
- **Frontend / Templating**: Jinja2 with HTML5, CSS3 (modern gym-themed dark styling, Flexbox layout, Google Fonts: Roboto).
- **Validation**: Pydantic v2.
- **Testing**: Pytest, HTTPX (`fastapi.testclient`), Playwright (E2E browser testing).

---

## 3. Project Directory Structure

```
FitBuddy/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point, mounts, lifespan
│   ├── routes.py                # Web form handlers and JSON REST API routes
│   ├── database.py              # SQLAlchemy DB models, session management, CRUD
│   ├── schemas.py               # Pydantic models for validation and serialization
│   ├── gemini_generator.py      # Gemini 1.5 Pro 7-day workout plan generator
│   ├── gemini_flash_generator.py# Gemini Flash nutrition tip generator
│   ├── updated_plan.py          # Gemini 1.5 Pro feedback-based plan refinement
│   └── nutrition.py             # Domain-specific nutritional helpers/constants
├── templates/
│   ├── index.html               # Homepage & user input form
│   ├── result.html              # Plan display, nutrition tip & feedback form
│   └── all_users.html           # Admin dashboard of users and plans
├── static/
│   ├── images/
│   │   └── gym-bg.jpg           # Gym-themed hero/background image
│   └── css/
│       └── style.css            # Responsive dark fitness styling
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures (in-memory SQLite DB, mock AI)
│   ├── test_database.py         # Unit tests for CRUD and ORM models
│   ├── test_ai_generators.py    # Unit tests for Gemini & fallback logic
│   ├── test_web_routes.py       # Integration tests for HTML endpoints
│   └── test_api_routes.py       # Integration tests for JSON API endpoints
├── tasks/
│   ├── plan.md                  # Implementation phase plan
│   └── todo.md                  # Task-by-task execution checklist
├── .env.example                 # Template for GOOGLE_API_KEY & settings
├── requirements.txt             # Locked project dependencies
├── PLAN.md                      # This specification & architecture document
└── FitBuddy – AI Fitness Plan Generator using Gemini Models.docx
```

---

## 4. Data Models & Database Design

### 4.1 ORM Models (`app/database.py`)

#### Table: `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Explicit User ID supplied by user (or auto-assigned) |
| `name` | String(100) | Not Null | User full name |
| `age` | Integer | Not Null | User age in years |
| `weight` | Float | Not Null | User weight in kilograms |
| `goal` | String(100) | Not Null | User fitness goal (e.g. weight loss, muscle gain) |
| `intensity` | String(50) | Not Null | Intensity level (Low, Medium, High) |
| `schedule` | Integer | Default 7 | Duration of workout plan in days |

#### Table: `workout_plans`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-increment | Internal plan ID |
| `user_id` | Integer | ForeignKey(`users.id`), Unique, Indexed | Reference to user |
| `original_plan` | Text | Nullable | Initial Gemini 1.5 Pro generated plan |
| `updated_plan` | Text | Nullable, Default None | Feedback-revised Gemini 1.5 Pro plan |

### 4.2 Database Helper Functions
- `save_user(user_id: int, name: str, age: int, weight: float, goal: str, intensity: str) -> User`: Upserts user details (creates if not exists, updates if exists).
- `save_plan(user_id: int, plan: str) -> WorkoutPlan`: Stores or replaces the original plan for a user.
- `update_plan(user_id: int, updated_text: str) -> WorkoutPlan`: Persists the feedback-revised plan.
- `get_original_plan(user_id: int) -> Optional[str]`: Retrieves original plan text.
- `get_user(user_id: int) -> Optional[User]`: Retrieves user by ID.
- `get_all_users() -> List[User]`: Fetches all user records.
- `get_all_plans() -> List[WorkoutPlan]`: Fetches all workout plans.
- `delete_user(user_id: int) -> bool`: Cascades delete of user and associated plans for admin cleanups.

---

## 5. Pydantic Schemas (`app/schemas.py`)

- `UserInput`:
  - `user_id: int`
  - `username: str`
  - `age: int` (gt=0, lt=130)
  - `weight: float` (gt=0.0)
  - `goal: str`
  - `intensity: str` (e.g., 'Low', 'Medium', 'High')
- `WorkoutRequest`:
  - `goal: str`
  - `intensity: str`
- `FeedbackRequest`:
  - `feedback: str`
- `WorkoutResponse`:
  - `model: str`
  - `workout_plan: str`
- `NutritionResponse`:
  - `goal: str`
  - `nutrition_tip: str`
- `PlanGenerationResponse`:
  - `message: str`
  - `workout_plan: str`

---

## 6. AI Prompt Design & Fallback Engineering

### 6.1 Gemini 1.5 Pro: 7-Day Workout Generation (`app/gemini_generator.py`)
- **System Prompt / Structure**:
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

### 6.2 Gemini Flash: Targeted Nutrition Tip (`app/gemini_flash_generator.py`)
- **System Prompt / Structure**:
  ```text
  Give one clear, helpful nutrition or recovery tip for someone focused on '{goal}'.
  The tip should be practical, friendly, and easy to understand.
  ```

### 6.3 Gemini 1.5 Pro: Feedback-Driven Refinement (`app/updated_plan.py`)
- **System Prompt / Structure**:
  ```text
  You are a professional fitness trainer assistant.
  Here's the original 7-day workout plan:
  {original_plan}

  User Feedback:
  "{user_feedback}"

  Based on the feedback, revise the relevant parts of the workout plan. Keep the format and rest of the plan unchanged if not needed.
  ```

### 6.4 Offline / Resilient Fallback Engine
- When `GOOGLE_API_KEY` is not present, invalid, or hits quota limits, the application automatically engages a deterministic fallback generator tailored to the goal (`weight loss`, `muscle gain`, `general fitness`, `flexibility`) and intensity. This guarantees 100% uptime for local evaluation and automated testing.

---

## 7. Routes & Interfaces (`app/routes.py`)

### 7.1 Web Interface Routes (Jinja2 HTML)
1. `GET /`: Renders `index.html` with the workout generator form.
2. `POST /generate-workout`:
   - Accepts form data: `username`, `user_id`, `age`, `weight`, `goal`, `intensity`.
   - Invokes `save_user(...)`.
   - Calls `generate_workout_gemini(...)` and `generate_nutrition_tip_with_flash(...)`.
   - Invokes `save_plan(...)`.
   - Returns `result.html` populated with user details, workout plan (`<pre>`), and nutrition tip.
3. `POST /submit-feedback`:
   - Accepts form data: `user_id`, `feedback`.
   - Retrieves original plan via `get_original_plan(user_id)`.
   - Calls `update_workout_plan(original_plan, feedback)`.
   - Updates record via `update_plan(user_id, updated_plan)`.
   - Re-renders `result.html` with user info, updated plan, nutrition tip, and success message: *"Your plan has been updated based on your feedback!"*.
4. `GET /view-all-users`:
   - Queries users and plans.
   - Renders `all_users.html` with a table: User ID, Name, Age, Weight, Goal, Intensity, Original Plan (`<pre>`), Updated Plan (`<pre>`), and Actions.
5. `POST /delete-user/{user_id}`:
   - Deletes specified user and plans, redirects back to `/view-all-users`.

### 7.2 REST API Endpoints (JSON)
1. `POST /generate-workout/gemini` -> Accepts `WorkoutRequest`, returns `{"model": "gemini-pro", "workout_plan": str}`.
2. `GET /nutrition-tip` -> Query param `?goal=...`, returns `{"goal": str, "nutrition_tip": str}`.
3. `POST /generate-plan` -> Accepts `UserInput`, creates user and plan, returns `{"message": str, "workout_plan": str}`.
4. `POST /update-plan/{user_id}` -> Accepts `FeedbackRequest`, updates plan, returns `{"updated_plan": str}`.
5. `GET /api/users` -> Returns list of all user objects with plans.

---

## 8. Frontend UI Specification

### 8.1 Visual Aesthetic & Design System
- **Theme**: Premium dark fitness interface (`#0d1117` background, `#161b22` cards, `#21262d` borders).
- **Accents**: Athletic Orange (`#f97316`), Electric Cyan (`#06b6d4`), Success Green (`#10b981`).
- **Typography**: Google Fonts `'Roboto', sans-serif`, clear hierarchy, legible monospace `<pre>` container for formatted workout routines.
- **Card Styling**: Rounded corners (`12px`), subtle box-shadows, responsive container widths (max-width `900px`).
- **Hero/Background Image**: `static/images/gym-bg.jpg` with a dark overlay to maintain readability.

### 8.2 Pages
- `index.html`: Clean, centered card with 6 input fields (Name, User ID, Age, Weight, Goal dropdown/input, Intensity dropdown), Submit button.
- `result.html`:
  - User Summary Card (Name, ID, Age, Weight, Goal, Intensity).
  - 7-Day Workout Plan card with `<pre>` formatting.
  - Nutrition Tip Card with accent highlighting.
  - Feedback Form card (User ID pre-filled or requested, textarea for feedback, Submit Feedback button).
  - Confirmation alert banner when redirected after feedback.
  - Navigation links: "Generate New Plan" & "Admin: View All Users".
- `all_users.html`:
  - Admin Header with count of registered users.
  - Responsive table showing all 8 columns: ID, Name, Age, Weight, Goal, Intensity, Original Plan, Updated Plan.
  - Delete action button per row.
  - Navigation link back to Home (`/`).

---

## 9. Verification & Quality Gates

1. **Database Gate**: Validate SQLite schema creation, foreign key constraints, and CRUD operations via Pytest.
2. **AI Engine Gate**: Verify prompts, responses, error handling, and fallback behavior with and without API keys.
3. **API & Route Gate**: Integration tests verifying status 200, proper HTML rendering, form submission redirects, and REST API contracts.
4. **End-to-End Browser Gate**: DevTools / Playwright test confirming full user journey:
   - Load homepage -> fill form -> generate plan -> check result page.
   - Submit feedback -> verify updated plan card & confirmation badge.
   - Load `/view-all-users` -> verify table contains new record with both original and updated plans.
