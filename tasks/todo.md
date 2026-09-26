# FitBuddy task checklist and verification log

## Task breakdown

- [x] Task 1: environment and scaffolding
  - Acceptance: `.venv` created, dependencies installed from `requirements.txt`, directories created
    (`app/`, `templates/`, `static/images/`, `tests/`).
  - Verify: `python3 -c "import fastapi, sqlalchemy, google.generativeai; print('OK')"` exits 0.
  - Files: `requirements.txt`, `.env.example`, `.env`, `static/images/gym-bg.jpg`.

- [x] Task 2: database layer
  - Acceptance: `User` and `WorkoutPlan` SQLAlchemy models plus the CRUD helpers `save_user`,
    `save_plan`, `update_plan`, `get_original_plan`, `get_user`, `get_all_users`, `delete_user`,
    persisting to SQLite.
  - Verify: `tests/test_database.py` passes.
  - Files: `app/database.py`, `tests/test_database.py`.

- [x] Task 3: validation schemas
  - Acceptance: `UserInput`, `WorkoutRequest`, `FeedbackRequest`, `WorkoutResponse`,
    `NutritionResponse` defined and validated.
  - Verify: schema tests pass.
  - Files: `app/schemas.py`.

- [x] Task 4: AI generators with fallback
  - Acceptance: `gemini_generator.py` (Pro), `gemini_flash_generator.py` (Flash), `updated_plan.py`
    (Pro revision) and `nutrition.py`, each with a Gemini call and a deterministic local fallback.
  - Verify: `tests/test_ai_generators.py` covers the keyed and keyless paths.
  - Files: the four modules plus `tests/test_ai_generators.py`.

- [x] Task 5: routes and application core
  - Acceptance: `app/routes.py` and `app/main.py` implement the HTML routes `/`, `/generate-workout`,
    `/submit-feedback`, `/view-all-users`, `/delete-user/{user_id}` and the JSON endpoints
    `/generate-workout/gemini`, `/nutrition-tip`, `/generate-plan`, `/update-plan/{user_id}`.
  - Verify: `tests/test_web_routes.py` and `tests/test_api_routes.py` pass.
  - Files: `app/main.py`, `app/routes.py`, both test modules.

- [x] Task 6: templates and styling
  - Acceptance: `index.html`, `result.html` and `all_users.html` built with the gym-photo layout, Roboto
    typography, `<pre>` plan blocks, a feedback form and a confirmation line.
  - Verify: rendered in a browser against the DOCX screenshots.
  - Files: the three templates and `static/css/style.css`.

- [x] Task 7: end-to-end browser verification
  - Acceptance: the journey runs in a live browser from home form to result, feedback, and dashboard.
  - Verify: the Playwright test opens the page, fills the form, clicks the buttons and asserts the DOM.
  - Files: `tests/test_e2e_browser.py`.

## Verification log

Suite result: 26 passed. Command: `PYTHONPATH=. python -m pytest tests/ -v`.

| Test module | Tests | Covers |
|---|---|---|
| `test_database.py` | 6 | ORM models, CRUD helpers, cascade delete |
| `test_schemas.py` | 5 | Pydantic validation, valid and invalid payloads |
| `test_ai_generators.py` | 4 | Gemini prompts and the local fallback |
| `test_api_routes.py` | 5 | JSON REST contracts |
| `test_web_routes.py` | 5 | HTML form routes and template rendering |
| `test_e2e_browser.py` | 1 | Full browser journey via Playwright |

Live server: `python -m uvicorn app.main:app --port 8010` started cleanly with no console errors.

Browser journey, checked against the DOCX screenshots:

| Step | Result |
|---|---|
| `GET /` renders the six-input form | Matches image24 |
| Submit the form, `POST /generate-workout` | 200, `result.html` rendered |
| User information card shows all six values | Matches image25 |
| Plan shows Day 1 to 7, each with warm-up, main workout and cooldown | Matches images16 and 23 |
| Nutrition tip is goal-aligned | Matches image14 |
| Submit feedback, `POST /submit-feedback` | 200, revision persisted |
| Confirmation text | "Your plan has been updated based on your feedback!", matching image22 |
| `GET /view-all-users` | Nine columns including both plans, matching image7 |
| `POST /delete-user/{id}` | 303 back to the dashboard, cascade delete confirmed |
| `GET /docs` | 200 |

REST contracts checked with curl: `/generate-workout/gemini`, `/nutrition-tip`, `/generate-plan`,
`/update-plan/{id}` including the error body, and `/api/users`. All return the documented shapes.

Responsive and accessibility checks:

| Check | Result |
|---|---|
| No horizontal overflow at 375px | `scrollWidth == 375` |
| Every form control has a label | All |
| One page-level `<h1>` per page | All three |
| `lang="en"` and a descriptive `<title>` | All three |
| Console errors or warnings | None |

### Defects found and fixed

1. **The test suite corrupted the development database.** Pytest teardown ran `drop_all` against the
   shared `fitbuddy.db`, which broke a running Uvicorn server and surfaced as an internal server error
   in the browser.
   Fixed in `tests/conftest.py`, which forces an isolated `DATABASE_URL` pointing at a temp file
   before any `app.*` module is imported, plus a session-scoped cleanup fixture. Confirmed the
   development database survives a full run.

2. **No `<h1>` on any page.** Added one per template with matching CSS, keeping `<h2>` for the card
   headings.

3. **E2E navigation assertions were flaky.** `wait_for_load_state` raced the commit and `to_have_url`
   treated the string as a literal. Replaced with `page.expect_navigation()` context managers and
   `expect(page).to_have_url(re.compile(...))`. Stable across repeated runs since.

4. **Admin table title used an en dash** where the DOCX shows a hyphen. Corrected to
   `FitBuddy - All Users & Workout Plans`.

5. **Mobile horizontal overflow on the result page** at 375px (`scrollWidth 440` against a 375px
   viewport, caused by the "View All Users" button), and container widths that did not scale.
   Fixed in `static/css/style.css` with `clamp()` spacing, fluid container widths, a wrapping header
   nav, stacked action buttons under 640px and a fluid page header. Verified with no page-level
   overflow at 320, 375, 480, 640, 768, 900, 1024, 1280, 1440, 1600 and 1920px on `/` and
   `/view-all-users`, and across the full journey at 320, 375, 768 and 1440px.

### Conformance pass

Re-checked the application against the DOCX and its 28 embedded screenshots, treating the images as
the visual specification.

### Defects found and fixed, second pass

6. **`static/images/gym-bg.jpg` was a screenshot of the app itself.** The file was byte-for-byte the
   DOCX home page capture at 1918x870, the photo plus the rendered card, heading and form. Used as a
   background it ghosted the old UI behind the live one on every page.
   Replaced with the photograph the original screens use
   (`images.unsplash.com/photo-1571019613454-1cb2f99b2d8b`, 1920x1280, Unsplash License, credited in
   the README). Because the bytes at that path changed, the URL is versioned as `gym-bg.jpg?v=2` so
   cached copies cannot survive.

7. **The interface had drifted to a dark theme.** The app shipped `#0f172a` and `#f97316` while every
   reference screen is light. `static/css/style.css` was rebuilt around the sampled palette and all
   three templates were restyled, including the admin column names `User ID` and `Weight (kg)`. The
   E2E header assertion was updated to match.

8. **The feedback form locked the user ID.** The reference shows an editable input; the implementation
   rendered a disabled field plus a hidden one. Replaced with a single editable input.

9. **Static assets were served with heuristic caching**, so CSS and image edits appeared to do nothing
   on reload. This masked defect 6 during verification.
   `app/main.py` now mounts `/static` through a `RevalidatedStaticFiles` subclass that adds
   `Cache-Control: no-cache, must-revalidate`, so assets are revalidated rather than served stale. A
   304 is still possible when nothing changed.

10. **Admin routes bypassed the spec's data helpers.** The DOCX specifies that `/view-all-users` calls
    `get_all_users()` and `get_all_plans()`, but both routes hand-rolled a second query while the
    helpers sat imported and unused.
    Both routes now build rows through a shared `_user_row()` helper, and the dead imports were
    dropped.

### Re-verified after the second pass

| Check | Result |
|---|---|
| Full pytest suite | 26 passed, including the Playwright E2E test |
| `GET /`, `/view-all-users`, `/docs`, `/static/css/style.css` | 200 |
| All five REST endpoints match the section 7.2 contracts | Verified with curl |
| Home, generate, feedback, dashboard, delete | Driven in a real browser |
| Plan contains Day 1 to 7 with warm-up, main workout and cooldown | Confirmed |
| Confirmation text matches the DOCX verbatim | Confirmed |
| Admin table has nine columns including both plans | Confirmed |
| Horizontal overflow at 320 to 1920px | None on `/` or `/view-all-users` |
| Failed sub-resource requests | None |
| One `<h1>` per page, every form control labelled | Confirmed |

## Measured-conformance pass (2026-09-26)

This pass re-derived every visual value from pixels in the DOCX screenshots instead of trusting the
previous pass's descriptions, then drove the whole application in a real in-app browser.

### Method

`gym-bg.jpg` is the same photograph the DOCX screenshots use, and both render with
`background-size: cover; background-position: center`. That makes the compositing invertible: for a
given reference pixel, look up the raw photo pixel at the same coordinate and solve
`out = raw*(1-a) + 255*a` for the white overlay alpha `a`. Headings too small to read at native size
were cropped and upscaled before identification.

### Defects found and fixed

11. **The background photograph was washed out by a gradient that should not exist.** `body` carried
    `linear-gradient(rgba(255,255,255,0.78) to 0.88)` over the image. Compositing the reference
    against the raw asset gives a mean implied alpha of -0.03 on the home page and 0.05 on the result
    page, so there is no overlay at all in the spec.
    Overlay removed. The photo now renders at full saturation.

12. **The admin dashboard was styled as a card over the photo.** The only UI reference for that page,
    `image7.png`, is flat: a `#f0f4f8` page with the table sitting directly on it. A colour histogram
    confirms it, with 1,123 distinct colours of which `#f9f9f9` and `#f0f4f8` cover 1.43 million
    pixels and no photographic content appears anywhere in the image.
    `all_users.html` now sets `body.page-flat`, the card wrapper is gone, and the table spans the page.

13. **Palette tokens were off the sampled values.** Corrected `--ink` from `#16202e` to `#1f2937` and
    added `--label-ink` at `#111827`. Form and table borders moved from `#cbd5e1` and `#dbe2ea` to
    `#cccccc`, card borders to `#e6e6e6`, placeholders from `#94a3b8` to `#757575`, the `<pre>` panel
    from `#f5f7fa` to `#f3f4f6`, the card radius from 16px to 24px, and the card alpha from 0.94 to
    0.95. The admin page background was added as `#f0f4f8`.

14. **The admin table was left-aligned throughout.** The reference centres the first six columns and
    left-aligns only the two plan columns, and it shows whole plans with no 220px scroller.
    `th` and `td` are now centred with a `.plan-col` override, and the `max-height` scroller was
    removed.

15. **The result page heading used the wrong emoji.** `image25.png` upscaled 4x shows the weightlifter
    rather than the flexed biceps the home page uses. Corrected in `result.html`.

16. **The confirmation message had a panel the reference does not have.** `image22.png` shows plain
    green text. `.alert-success` was reduced to green text with no background, border or left bar.

17. **The feedback textarea used the page font.** The reference renders it in monospace while the
    single-line inputs stay in Roboto. `textarea` was given `'Roboto Mono'`.

18. **The home form had four placeholders the reference does not show, and defaulted intensity to
    Medium.** `image24.png` shows Name, User ID, Age and Weight empty with the placeholder on Fitness
    Goal only, and the select reading `Low`. Both corrected.

19. **The feedback form pre-filled the user ID.** The reference shows the field empty with its
    placeholder visible, and the placeholder text only makes sense if the user types their ID.
    Pre-fill removed, and `tests/test_e2e_browser.py` updated to type the ID as the spec's flow
    requires.

### Re-verified after the third pass

Values sampled from the reference, then read back from the live page in the browser at a 1918px
viewport:

| Check | Reference | Rendered | Result |
|---|---|---|---|
| Card left and right edge | 538 / 1363 | 534 / 1370 | Match |
| Card width | 825px | 836px | Match |
| Card border and radius | `#e6e6e6`, ~24px | `#e6e6e6`, 24px | Match |
| Heading colour | `#1f2937` | `#1f2937` | Match |
| Label colour | `#111827` | `#111827` | Match |
| Field border and fill | `#cccccc`, `#ffffff` | `#cccccc`, `#ffffff` | Match |
| Button fill | `#3b82f6` | `#3b82f6` | Match |
| Table header | `#1e88e5` | `#1e88e5` | Match |
| Table cell border | `#cccccc` | `#cccccc` | Match |
| Admin page background | `#f0f4f8`, no image | `#f0f4f8`, `background-image: none` | Match |
| Plan `<pre>` panel | `#f3f4f6` | `#f3f4f6` | Match |
| Intensity default | `Low` | `Low` | Match |

Journey driven in the in-app browser at 1918x870, 820x1180 and 390x844: home form, generated plan
covering Day 1 to 7 with a warm-up, main workout and cooldown per day, a goal-aligned nutrition tip,
feedback reading "Please add more cardio and include yoga for recovery", a revised plan confirmed
containing `[Updated based on your feedback: ...]` plus the cardio and yoga adjustments with the
original preserved, an admin table listing both plans, and a delete that removed the record. No
horizontal overflow at any width tested.

Route contracts re-checked against the DOCX's own code screenshots in `image1`, `image13`, `image15`
and `image21`. All four API handlers match `app/routes.py` line for line, including
`POST /update-plan/{user_id}` returning HTTP 200 with `{"error": "Original plan not found for this
user."}`. That status code comes from a bare `return` in the spec's own code, so it is specified
behaviour rather than a defect.

Suite result: 26 passed, 0 skipped. The live server was up, so the Playwright journey ran instead of
skipping.

### Still deviating from the reference

Four elements appear in the app but in no DOCX screenshot: the header nav bar, the footer, the
"+ Register New User" button, and the subtitle under the home page heading. Without the nav the admin
dashboard and `/docs`, which scenario 4 depends on, would be reachable only by typing a URL. Each is a
one-line removal if that trade is reversed.

### Note on AI output

`GOOGLE_API_KEY` is still empty, so every plan, tip and revision in this pass came from the
deterministic local fallback described in `PLAN.md` section 6.4. The live Gemini path remains
unexercised, and the pinned model names `gemini-1.5-pro` and `gemini-1.5-flash` have been retired by
Google, so the path would fall back even with a key.
