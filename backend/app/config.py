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

# --- Phase 2: LLM generation core ---

# Prompt templates loaded by the prompt loader (02-02).
PROMPTS_DIR = REPO_ROOT / "prompts"

# Run logs: JSONL metadata written by the run-log writer (02-02). Gitignored.
LOGS_DIR = REPO_ROOT / "logs"
RUNS_LOG = LOGS_DIR / "runs.jsonl"

# Model slug is config-only (D-01/D-02): swapping models must never need a code
# change. Env-overridable so the fixture harness (02-04) can pin a test model.
LLM_MODEL = os.environ.get("LLM_MODEL", "anthropic/claude-sonnet-4.5")

# 1 call + 2 validation retries (D-04) — spend bound before any call site exists.
LLM_MAX_ATTEMPTS = 3

# --- Phase 6: LinkedIn ---

# Character limits (D-05, verified in 06-RESEARCH.md). Headline 220 / Sobre
# 2600 / Experiência 2000 are MEDIUM-confidence cross-source consensus —
# LinkedIn's official Help Center publishes NO numeric limits for these fields
# (negative evidence fetched and recorded in 06-RESEARCH.md). Skills count is
# HIGH — officially verified verbatim from LinkedIn Help ("You can add up to
# 100 skills to your profile"; the old 50 figure is stale). No safety margins:
# the counter mirrors LinkedIn's own entry fields, and over-limit output
# degrades gracefully by design (D-07 — flagged in place, never truncated).
LINKEDIN_HEADLINE_MAX_CHARS = 220
LINKEDIN_SOBRE_MAX_CHARS = 2600
LINKEDIN_EXPERIENCIA_MAX_CHARS = 2000
LINKEDIN_SKILLS_MAX_COUNT = 100  # HIGH confidence — officially verified
# Objetivo bounds (D-02): the one INPUT bound — mirrors the JD 80-char floor;
# the max is a sane token-cost guard at personal scale. Output bounds live
# post-generation only (D-07) — never in the LLM-layer models.
LINKEDIN_OBJETIVO_MIN_LENGTH = 80
LINKEDIN_OBJETIVO_MAX_LENGTH = 2000
