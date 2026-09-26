"""Shared fixtures: profile dict + file variants for schema and loader tests.

File fixtures write into pytest tmp_path — tests never touch the real
content/ directory (the backend is read-only over content/).
"""

import copy
from pathlib import Path

import pytest
import yaml

# Repo root, computed from this file's location:
# backend/tests/conftest.py -> backend/tests -> backend -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
SHIPPED_PROFILE_PATH = REPO_ROOT / "content" / "profile.md"


def minimal_profile() -> dict:
    """Smallest dict valid against the v1 schema (every other section defaults)."""
    return {
        "name": "Ana Exemplo",
        "contact": {"email": "ana.exemplo@example.com", "location": "São Paulo, SP"},
        "summary": {"pt-BR": "Resumo de exemplo.", "en": "Example summary."},
        "experiences": [
            {
                "company": "Exemplo IA",
                "title": {
                    "pt-BR": "Engenheira de Software Sênior",
                    "en": "Senior Software Engineer",
                },
                "start_date": "2022-03",
                "description": {"pt-BR": "Descrição de exemplo.", "en": "Example description."},
                "impacts": [
                    {
                        "action": {
                            "pt-BR": "Implementou um pipeline RAG com avaliação automática",
                            "en": "Implemented a RAG pipeline with automated evaluation",
                        },
                        "metric": {
                            "pt-BR": "-40% no tempo de resposta",
                            "en": "-40% response time",
                        },
                    }
                ],
            }
        ],
    }


def full_profile() -> dict:
    """All D-07 sections populated — mirrors the shipped example persona shape."""
    profile = minimal_profile()
    profile.update(
        {
            "example": True,
            "education": [
                {
                    "institution": "Universidade Exemplo",
                    "degree": "Bacharelado em Ciência da Computação",
                    "start_date": "2013-02",
                    "end_date": "2017-12",
                }
            ],
            "skills": [
                {"category": "linguagens", "items": ["Python", "TypeScript"]},
                {"category": "frameworks", "items": ["FastAPI", "React"]},
                {"category": "ferramentas", "items": ["Docker", "Git"]},
                {"category": "cloud", "items": ["AWS"]},
            ],
            "certifications": [
                {
                    "name": "AWS Certified Solutions Architect",
                    "issuer": "Amazon Web Services",
                    "year": "2023",
                }
            ],
            "languages": [
                {"name": "Português", "level": "nativo"},
                {"name": "Inglês", "level": "avançado"},
            ],
            "projects": [
                {
                    "name": "Assistente Exemplo",
                    "description": {
                        "pt-BR": "Chat de IA generativa para documentos internos.",
                        "en": "Generative-AI chat over internal documents.",
                    },
                    "technologies": ["FastAPI", "React"],
                    "impacts": [],
                }
            ],
        }
    )
    return profile


def _write_profile(directory: Path, meta: dict) -> Path:
    """Write a profile.md variant (YAML frontmatter + minimal body) into directory."""
    text = (
        "---\n"
        + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + "Perfil de teste.\n"
    )
    path = directory / "profile.md"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def minimal_profile_data() -> dict:
    """A fresh deep copy per test — mutations never leak between tests."""
    return copy.deepcopy(minimal_profile())


@pytest.fixture
def valid_profile_path(tmp_path: Path) -> Path:
    """A complete, valid profile file."""
    return _write_profile(tmp_path, full_profile())


@pytest.fixture
def typo_profile_path(tmp_path: Path) -> Path:
    """Typo'd TOP-LEVEL key: `experiances:` (D-10's canonical example)."""
    profile = full_profile()
    profile["experiances"] = []
    return _write_profile(tmp_path, profile)


@pytest.fixture
def nested_typo_profile_path(tmp_path: Path) -> Path:
    """Typo'd key INSIDE a nested experience: `salario` (extra_forbidden)."""
    profile = full_profile()
    profile["experiences"][0]["salario"] = "1.000.000"
    return _write_profile(tmp_path, profile)


@pytest.fixture
def missing_ptbr_profile_path(tmp_path: Path) -> Path:
    """A localized field (summary) missing the base language pt-BR (D-03/D-04)."""
    profile = full_profile()
    profile["summary"] = {"en": "Summary without the base language."}
    return _write_profile(tmp_path, profile)


@pytest.fixture
def broken_yaml_profile_path(tmp_path: Path) -> Path:
    """Raw broken YAML frontmatter — must surface as ProfileError, never a stack trace."""
    text = (
        "---\n"
        "example: true\n"
        "name: [unclosed\n"
        "  bad: {mixed\n"
        "---\n"
        "\nCorpo.\n"
    )
    path = tmp_path / "profile.md"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def non_utf8_profile_path(tmp_path: Path) -> Path:
    """Bytes that are not valid UTF-8 (Pitfall 7: Windows encoding discipline)."""
    path = tmp_path / "profile.md"
    path.write_bytes(b"---\nname: \xff\xfe broken\n---\n")
    return path
