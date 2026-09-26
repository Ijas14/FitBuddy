import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.routes import router

# Ensure database tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FitBuddy – AI Fitness Plan Generator",
    description="Personalized workout plans and nutrition tips generated with Google Gemini AI models.",
    version="1.0.0",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

class RevalidatedStaticFiles(StaticFiles):
    """Serve static assets with revalidation so edits show up on reload.

    Starlette already emits ETag/Last-Modified, but browsers may reuse a
    heuristic-cached copy without revalidating, which makes stylesheet and
    image edits look like they had no effect.  ``no-cache`` still permits a
    304, so unchanged assets cost one conditional request and nothing more.
    """

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response


# Mount static files directory
if os.path.exists(STATIC_DIR):
    app.mount("/static", RevalidatedStaticFiles(directory=STATIC_DIR), name="static")

# Include all web and REST routes
app.include_router(router)
