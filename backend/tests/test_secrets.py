"""SC5 / T-01-01: the OpenRouter key file must never be committable.

`git check-ignore .env` must exit 0 (the file is ignored) and `.env` must
never appear in `git ls-files` (the file is not tracked). Both checks run
against the repo root so they are independent of pytest's cwd.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # backend/tests/ -> repo root


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_env_is_gitignored() -> None:
    """`.env` must be covered by .gitignore (check-ignore exits 0)."""
    result = _git("check-ignore", ".env")
    assert result.returncode == 0, (
        f".env is not gitignored (exit {result.returncode}): {result.stderr.strip()}"
    )


def test_env_is_not_tracked() -> None:
    """`.env` must not appear in the tracked file list."""
    result = _git("ls-files")
    assert result.returncode == 0, f"git ls-files failed: {result.stderr.strip()}"
    tracked = result.stdout.splitlines()
    assert ".env" not in tracked, ".env is tracked in git — secret leak risk (SC5 broken)"
