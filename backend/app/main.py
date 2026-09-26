"""FastAPI app entrypoint.

Registration order matters (Pitfall 5): ALL /api routes are registered FIRST;
the SPA StaticFiles mount owns every remaining path and must be LAST.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIST
from app.routes.profile import router as profile_router
from app.routes.resume import router as resume_router

app = FastAPI(title="Career Tailor")

# API routes FIRST — anything registered after the "/" mount is unreachable.
app.include_router(profile_router)
app.include_router(resume_router)  # before the SPA mount (Pitfall 3/5)

# Daily-use single process: serve the built SPA (frontend/dist) at "/".
# Guarded so dev-only sessions (no build yet) don't crash at import.
if FRONTEND_DIST.exists():  # Pitfall 5: mount LAST
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIST), html=True),
        name="spa",
    )
