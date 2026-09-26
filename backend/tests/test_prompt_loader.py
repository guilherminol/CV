"""Prompt loader tests — every failure mode is a loud PromptError naming the
file (PROFILE-03 ergonomics; mirrors tests/test_loader.py).

RED-first (plan 02-02 Task 1): app/llm does not exist yet — these MUST fail.
Negative cases write into tmp_path and retarget via the prompts_dir parameter;
only the happy-path test reads the real prompts/keyword-extraction.md.
"""

from pathlib import Path

import pytest
import yaml

from app.llm.errors import PromptError
from app.llm.prompts import load_prompt

# Repo root: backend/tests -> backend -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_prompt(directory: Path, meta: dict, body: str = "System prompt.") -> Path:
    """Write a <id>.md prompt file (YAML frontmatter + body) into directory."""
    directory.mkdir(parents=True, exist_ok=True)
    text = (
        "---\n"
        + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + body
        + "\n"
    )
    path = directory / f"{meta['id']}.md"
    path.write_text(text, encoding="utf-8")
    return path


def _valid_meta() -> dict:
    return {"id": "keyword-extraction", "temperature": 0.2, "max_tokens": 2000}


# ---------------------------------------------------------------------------
# Happy path — the real shipped prompt file (SC: first real meta-prompt)
# ---------------------------------------------------------------------------


def test_load_real_keyword_extraction_prompt() -> None:
    loaded = load_prompt("keyword-extraction")  # real prompts/ dir at repo root
    assert loaded.spec.id == "keyword-extraction"
    assert isinstance(loaded.spec.temperature, float)
    assert loaded.spec.max_tokens > 0
    assert loaded.body.strip()  # body IS the system prompt payload (D-07)
    assert "{{" not in loaded.body  # D-07: no template variables


def test_valid_prompt_in_tmp_dir(tmp_path: Path) -> None:
    _write_prompt(tmp_path, _valid_meta(), body="Extraia palavras-chave.")
    loaded = load_prompt("keyword-extraction", prompts_dir=tmp_path)
    assert loaded.spec.temperature == 0.2
    assert "palavras-chave" in loaded.body


# ---------------------------------------------------------------------------
# Failure modes → loud PromptError naming the offending key AND file (D-06)
# ---------------------------------------------------------------------------


def test_typo_key_names_key_and_file(tmp_path: Path) -> None:
    meta = _valid_meta()
    meta["temperatura"] = 0.2  # typo'd key — extra="forbid" must catch it
    del meta["temperature"]
    path = _write_prompt(tmp_path, meta)
    with pytest.raises(PromptError) as excinfo:
        load_prompt("keyword-extraction", prompts_dir=tmp_path)
    msg = excinfo.value.message_ptbr
    assert "temperatura" in msg  # the exact offending key is named (D-06)
    assert str(path) in msg  # AND the file is named (PROFILE-03)
    assert excinfo.value.raw  # terminal-only detail preserved (D-13/D-14)
    assert "Extra inputs are not permitted" not in msg  # no English prose in UI path


def test_missing_file_names_path(tmp_path: Path) -> None:
    with pytest.raises(PromptError) as excinfo:
        load_prompt("nao-existe", prompts_dir=tmp_path)
    assert "não encontrado" in excinfo.value.message_ptbr
    assert str(tmp_path / "nao-existe.md") in excinfo.value.message_ptbr


def test_invalid_yaml_mentions_yaml(tmp_path: Path) -> None:
    text = "---\nid: [unclosed\n  bad: {mixed\n---\n\nCorpo.\n"
    path = tmp_path / "keyword-extraction.md"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(PromptError) as excinfo:
        load_prompt("keyword-extraction", prompts_dir=tmp_path)
    msg = excinfo.value.message_ptbr
    assert "YAML" in msg
    assert str(path) in msg
    assert excinfo.value.raw


# ---------------------------------------------------------------------------
# Fresh read per call — no caching (D-08/SC1)
# ---------------------------------------------------------------------------


def test_edit_between_calls_is_reflected(tmp_path: Path) -> None:
    _write_prompt(tmp_path, _valid_meta(), body="Versão 1.")
    first = load_prompt("keyword-extraction", prompts_dir=tmp_path)
    assert "Versão 1." in first.body
    _write_prompt(tmp_path, _valid_meta(), body="Versão 2.")
    second = load_prompt("keyword-extraction", prompts_dir=tmp_path)
    assert "Versão 2." in second.body  # D-08/SC1: fresh read, no cache
