"""Central app configuration: paths + tolerant secret read.

The app must RUN with an empty or missing OPENROUTER_API_KEY — Phase 1 never
uses the key (ASVS V14; see .planning RESEARCH Security Domain).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/app/config.py -> backend/app -> backend -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

# Tolerant load: .env is gitignored and optional — empty/absent key is fine.
load_dotenv(REPO_ROOT / ".env")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

CONTENT_DIR = REPO_ROOT / "content"
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
