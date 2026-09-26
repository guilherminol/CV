"""Phase 2 wave-0 config: LLM constants, llm pytest marker, offline-by-default addopts."""

import tomllib
from pathlib import Path

import app.config as cfg

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_phase2_constants_exist_with_expected_defaults():
    assert cfg.LLM_MAX_ATTEMPTS == 3
    assert cfg.LLM_MODEL == "anthropic/claude-sonnet-4.5"
    assert cfg.PROMPTS_DIR == cfg.REPO_ROOT / "prompts"
    assert cfg.LOGS_DIR == cfg.REPO_ROOT / "logs"
    assert cfg.RUNS_LOG == cfg.LOGS_DIR / "runs.jsonl"


def test_llm_marker_registered_and_deselected_by_default():
    with open(BACKEND_DIR / "pyproject.toml", "rb") as f:
        opts = tomllib.load(f)["tool"]["pytest"]["ini_options"]
    assert any(m.startswith("llm:") for m in opts.get("markers", []))
    assert opts.get("addopts") == "-m 'not llm'"


def test_openai_sdk_is_dependency():
    with open(BACKEND_DIR / "pyproject.toml", "rb") as f:
        deps = tomllib.load(f)["project"]["dependencies"]
    assert any(d.split(">=")[0].strip() == "openai" for d in deps)
