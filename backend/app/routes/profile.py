"""GET /api/profile — status envelope, never HTTP 500 (D-12/D-13/D-15).

A broken profile is a UI-rendered state: the API answers 200 with a status
envelope; the full raw technical detail goes to the uvicorn terminal log only.
"""

import logging

from fastapi import APIRouter

from app.profile.completeness import compute_completude
from app.profile.loader import ProfileError, load_profile

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/profile")
def get_profile() -> dict:
    try:
        profile = load_profile()  # fresh load per request — no cache (D-15)
    except ProfileError as exc:
        logger.error("Falha ao carregar perfil:\n%s", exc.raw)  # raw detail → terminal (D-13)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
    return {
        "status": "ok",
        "exemplo": profile.example,  # D-11 placeholder flag
        "perfil": profile.model_dump(),
        # D-12: section presence/counts, computed fresh alongside the load
        "completude": compute_completude(profile),
    }
