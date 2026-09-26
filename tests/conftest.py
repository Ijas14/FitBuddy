"""
Shared pytest configuration for FitBuddy.

The test suite MUST NOT touch the development/production SQLite file
(``fitbuddy.db``).  ``app.database`` resolves ``DATABASE_URL`` at *import*
time, so the isolated value has to be injected here — ``conftest.py`` is
imported by pytest before any test module (and therefore before any
application module).

Without this isolation, a test teardown that drops tables would silently
break a concurrently running ``uvicorn`` dev server.
"""

import os
import tempfile

# --- Database isolation (must happen before `app.*` is imported) ------------
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "fitbuddy_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

# --- Keep the test suite off the Gemini API ---------------------------------
# The generators no longer fall back; without a key they raise GeminiError.
# Assign an empty string rather than popping the name: the `app.gemini_*`
# modules call `load_dotenv()` at import time, and `load_dotenv()` does not
# override variables that already exist. Popping the key therefore let `.env`
# re-populate it, so a developer with a real key in `.env` got a test suite
# that quietly called Gemini and consumed real quota.
os.environ["GOOGLE_API_KEY"] = ""

# Remove any leftover test database from a previous run.
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _dispose_engine():
    """Dispose the SQLAlchemy engine and remove the test DB at session end."""
    yield
    from app.database import engine

    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
