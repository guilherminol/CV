"""Per-section regeneration pipeline tests — run_linkedin_section_regen +
SECTION_STAGE_BY_ID (plan 06-02, D-04 Phase 5 semantics), OFFLINE.

Pinned here, via a ScriptedClient recording every create() kwargs (copied
verbatim from tests/test_resume_regen_pipeline.py's D-16 house pattern) and a
retargeted PROFILE_PATH (D-15 seam):

- (a) exactly ONE gateway stage runs per regen — the section's own stage
  (SECTION_STAGE_BY_ID); sibling stages never run — for ALL FOUR secao ids;
- (b) sibling byte-identity: only the target key is replaced in the merged
  secoes — sibling values come back equal (== and the same string objects)
  to what was submitted (D-04/Phase 5 SC1 semantics);
- (c) the experiências GROUP swap replaces the whole entries list
  (re-aligned to profile order) while headline/sobre/habilidades are
  untouched;
- (d) hint-as-DATA: an optional dica appears ONLY inside the composed user
  message (messages[1]); the system message (messages[0]) is the untouched
  prompt-file body; runs.jsonl stays metadata-only (T-06-01, Phase 5
  T-05-04 discipline);
- (e) blank/None dica is normalized away at the compose boundary — the user
  message equals the plain compose_linkedin_stage_input composition;
- (f) limites recomputed over the FULL merged state (a submitted sibling's
  over-limit text still surfaces in the regen response);
- (g) loud-empty contracts re-run on the regenerated block only.
"""

import json
from pathlib import Path

import pytest
import yaml

from app.llm.errors import LLMError
from app.llm.gateway import load_prompt
from app.llm.schemas import ExperienciaLinkedin
from app.linkedin.models import LinkedinSecoes
from app.resume.facts import compose_stage_input, serialize_profile_facts
from conftest import full_profile
from app.profile.models import Profile

# ---------------------------------------------------------------------------
# Offline fakes — copied verbatim from tests/test_resume_regen_pipeline.py
# (the D-16 house pattern)
# ---------------------------------------------------------------------------


class _FakeUsage:
    prompt_tokens = 120
    completion_tokens = 80
    total_tokens = 200


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": content})()})()]
        self.usage = _FakeUsage()
        self.cost = None


class ScriptedClient:
    """Fake returning a scripted SEQUENCE of contents / exceptions — one per
    attempt — recording every create() call."""

    def __init__(self, script: list):
        self._script = list(script)
        self.calls: list[dict] = []
        chat = type("Chat", (), {})()
        completions = type("Completions", (), {})()

        def create(**kwargs):
            self.calls.append(kwargs)
            item = self._script.pop(0)
            if isinstance(item, Exception):
                raise item
            return _FakeResponse(item)

        completions.create = create
        chat.completions = completions
        self.chat = chat


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline suite: a fake key satisfies the call-time guard (D-16)."""
    monkeypatch.setattr("app.llm.gateway.OPENROUTER_API_KEY", "test-key-offline")


# ---------------------------------------------------------------------------
# Canned content (UTF-8 accents survive the JSON round-trip) + shared inputs
# ---------------------------------------------------------------------------

OBJETIVO_REGEN = (
    "Crescer como engenheiro de dados sênior com foco em Python, SQL e "
    "plataformas de dados em nuvem, liderando iniciativas que impactem o negócio."
)

SUBMITTED_HEADLINE = "Headline em exibição — Python e dados em nuvem"
SUBMITTED_SOBRE = "Sobre em exibição " + "x" * 2600  # over the 2600 limit
SUBMITTED_EXPERIENCIA_DESCRICAO = "Descrição de experiência em exibição."
SUBMITTED_HABILIDADES = ["Habilidade antiga"]

NEW_HEADLINE_CONTENT = json.dumps(
    {"headline": "Novo headline gerado — Python, SQL e dados em nuvem"},
    ensure_ascii=False,
)
NEW_SOBRE_CONTENT = json.dumps(
    {"sobre": "Novo sobre gerado com foco em dados e impacto medido."},
    ensure_ascii=False,
)
NEW_EXPERIENCIAS_CONTENT = json.dumps(
    {
        "experiencias": [
            {
                "company": "Outra Corp",
                "title": "Analista de Dados",
                "descricao": "DESC-OUTRA-NOVA",
            },
            {
                "company": "Exemplo IA",
                "title": "Engenheira de Software Sênior",
                "descricao": "DESC-IA-NOVA",
            },
        ]
    },
    ensure_ascii=False,
)
NEW_SKILLS_CONTENT = json.dumps(
    {"habilidades": ["Python", "Docker", "FastAPI"]},
    ensure_ascii=False,
)

# secao → (gateway stage, wire-schema name, canned regen output for that stage)
REGEN_TARGETS = [
    ("headline", "linkedin-headline", "linkedin_headline", NEW_HEADLINE_CONTENT),
    ("sobre", "linkedin-sobre", "linkedin_sobre", NEW_SOBRE_CONTENT),
    ("experiencias", "linkedin-experiencias", "linkedin_experiencias", NEW_EXPERIENCIAS_CONTENT),
    ("habilidades", "linkedin-skills", "linkedin_skills", NEW_SKILLS_CONTENT),
]


def _submitted() -> LinkedinSecoes:
    """The displayed state a client would re-post: an over-limit sibling
    sobre, one experience entry, and a stale habilidades list."""
    return LinkedinSecoes(
        headline=SUBMITTED_HEADLINE,
        sobre=SUBMITTED_SOBRE,
        experiencias=[
            ExperienciaLinkedin(
                company="Exemplo IA",
                title="Engenheira de Software Sênior",
                descricao=SUBMITTED_EXPERIENCIA_DESCRICAO,
            )
        ],
        habilidades=list(SUBMITTED_HABILIDADES),
    )


def _two_experience_profile_path(tmp_path: Path) -> Path:
    """A profile whose experiences are [Exemplo IA, Outra Corp] — the group
    swap vector replaces a MULTI-entry list."""
    profile = full_profile()
    profile["experiences"] = profile["experiences"] + [
        {
            "company": "Outra Corp",
            "title": {"pt-BR": "Analista de Dados", "en": "Data Analyst"},
            "start_date": "2019-01",
            "description": {"pt-BR": "Descrição Outra Corp.", "en": "Outra Corp description."},
        }
    ]
    text = (
        "---\n"
        + yaml.safe_dump(profile, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + "Perfil de teste.\n"
    )
    path = tmp_path / "profile.md"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def _profile_path(monkeypatch: pytest.MonkeyPatch, valid_profile_path: Path) -> None:
    """Loader seam: load_profile() re-resolves PROFILE_PATH at call time (D-15)."""
    monkeypatch.setattr("app.profile.loader.PROFILE_PATH", valid_profile_path)


@pytest.fixture
def _two_exp_profile_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    path = _two_experience_profile_path(tmp_path)
    monkeypatch.setattr("app.profile.loader.PROFILE_PATH", path)
    return path


# ---------------------------------------------------------------------------
# (a) Exactly ONE stage per regen — the section's own stage (D-04)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("secao", "stage", "wire", "content"), REGEN_TARGETS)
def test_run_linkedin_section_regen_runs_exactly_one_stage(
    secao: str,
    stage: str,
    wire: str,
    content: str,
    tmp_path: Path,
    _profile_path: None,
) -> None:
    from app.linkedin.pipeline import run_linkedin_section_regen

    client = ScriptedClient([content])
    envelope = run_linkedin_section_regen(
        OBJETIVO_REGEN,
        "pt-BR",
        secao,
        _submitted(),
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )
    assert len(client.calls) == 1  # siblings + extraction NEVER run (D-04)
    call_wire = client.calls[0]["response_format"]["json_schema"]
    assert call_wire["name"] == wire
    assert call_wire["strict"] is True
    assert envelope["status"] == "ok"
    assert envelope["idioma"] == "pt-BR"
    assert set(envelope) == {"status", "idioma", "secoes", "limites"}
    assert set(envelope["secoes"]) == {"headline", "sobre", "experiencias", "habilidades"}


# ---------------------------------------------------------------------------
# (b) Sibling byte-identity — only the target key is replaced (D-04/SC1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("secao", "stage", "_wire", "content"), REGEN_TARGETS)
def test_siblings_byte_identical_only_target_replaced(
    secao: str,
    stage: str,
    _wire: str,
    content: str,
    tmp_path: Path,
    _profile_path: None,
) -> None:
    from app.linkedin.pipeline import run_linkedin_section_regen

    submitted = _submitted()
    client = ScriptedClient([content])
    envelope = run_linkedin_section_regen(
        OBJETIVO_REGEN,
        "pt-BR",
        secao,
        submitted,
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )
    secoes = envelope["secoes"]

    if secao == "headline":
        assert secoes["headline"] == json.loads(NEW_HEADLINE_CONTENT)["headline"]
    else:
        assert secoes["headline"] == submitted.headline
        assert secoes["headline"] is submitted.headline  # same string object

    if secao == "sobre":
        assert secoes["sobre"] == json.loads(NEW_SOBRE_CONTENT)["sobre"]
    else:
        assert secoes["sobre"] == submitted.sobre
        assert secoes["sobre"] is submitted.sobre

    if secao == "experiencias":
        assert secoes["experiencias"] != [entry.model_dump() for entry in submitted.experiencias]
    else:
        assert secoes["experiencias"] == [entry.model_dump() for entry in submitted.experiencias]
        assert secoes["experiencias"][0]["company"] is submitted.experiencias[0].company
        assert secoes["experiencias"][0]["descricao"] is submitted.experiencias[0].descricao

    if secao == "habilidades":
        assert secoes["habilidades"] == json.loads(NEW_SKILLS_CONTENT)["habilidades"]
    else:
        assert secoes["habilidades"] == list(submitted.habilidades)
        assert secoes["habilidades"][0] is submitted.habilidades[0]


# ---------------------------------------------------------------------------
# (c) Experiências GROUP swap — the whole list replaced, profile order
# ---------------------------------------------------------------------------


def test_experiencias_group_swap_replaces_whole_list_in_profile_order(
    tmp_path: Path, _two_exp_profile_path: Path
) -> None:
    from app.linkedin.pipeline import run_linkedin_section_regen

    submitted = LinkedinSecoes(
        headline=SUBMITTED_HEADLINE,
        sobre="Sobre em exibição, dentro do limite.",
        experiencias=[
            ExperienciaLinkedin(
                company="Exemplo IA",
                title="Engenheira de Software Sênior",
                descricao=SUBMITTED_EXPERIENCIA_DESCRICAO,
            ),
            ExperienciaLinkedin(
                company="Outra Corp",
                title="Analista de Dados",
                descricao="Descrição Outra Corp antiga.",
            ),
        ],
        habilidades=list(SUBMITTED_HABILIDADES),
    )
    client = ScriptedClient([NEW_EXPERIENCIAS_CONTENT])
    envelope = run_linkedin_section_regen(
        OBJETIVO_REGEN,
        "pt-BR",
        "experiencias",
        submitted,
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )
    entries = envelope["secoes"]["experiencias"]
    # The WHOLE submitted list is gone — replaced by the stage output,
    # re-aligned into PROFILE order (Exemplo IA first) by company fold-match.
    assert [entry["descricao"] for entry in entries] == ["DESC-IA-NOVA", "DESC-OUTRA-NOVA"]
    assert all(
        entry["descricao"] != SUBMITTED_EXPERIENCIA_DESCRICAO for entry in entries
    )
    # Siblings untouched while the group swapped.
    assert envelope["secoes"]["headline"] is submitted.headline
    assert envelope["secoes"]["sobre"] is submitted.sobre
    assert envelope["secoes"]["habilidades"] is submitted.habilidades or (
        envelope["secoes"]["habilidades"] == list(submitted.habilidades)
    )
    # limites recomputed over the merged state — index-aligned with the NEW list.
    assert [lim["limite"] for lim in envelope["limites"]["experiencias"]] == [2000, 2000]
    assert envelope["limites"]["experiencias"][0]["tamanho"] == len("DESC-IA-NOVA")


# ---------------------------------------------------------------------------
# (d) Hint-as-DATA — user message only; system prompt + runs.jsonl untouched
# ---------------------------------------------------------------------------


def test_dica_travels_as_user_message_data_system_and_log_untouched(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_section_regen

    dica = "destacar experiência com métricas de impacto"
    runs_log = tmp_path / "runs.jsonl"
    client = ScriptedClient([NEW_SKILLS_CONTENT])
    run_linkedin_section_regen(
        OBJETIVO_REGEN,
        "pt-BR",
        "habilidades",
        _submitted(),
        dica=dica,
        runs_log=runs_log,
        client=client,
    )
    (call,) = client.calls
    # Unchanged create() field set — the gateway seam is untouched.
    assert set(call) == {
        "model",
        "messages",
        "temperature",
        "max_tokens",
        "response_format",
        "extra_body",
    }
    messages = call["messages"]
    assert [m["role"] for m in messages] == ["system", "user"]
    # The hint lands in the USER message as DATA (D-15 Phase 5 pattern)...
    user = messages[1]["content"]
    assert "DICA DE DIRECIONAMENTO" in user
    assert dica in user
    assert "FATOS DO PERFIL:" in user
    assert OBJETIVO_REGEN in user
    # ...while the SYSTEM message is the untouched prompt-file body.
    system = messages[0]["content"]
    assert system == load_prompt("linkedin-skills").body
    assert "DICA" not in system
    assert dica not in system
    # runs.jsonl stays metadata-only — the hint never reaches it (T-05-04).
    log_text = runs_log.read_text(encoding="utf-8")
    assert dica not in log_text
    assert "DICA DE DIRECIONAMENTO" not in log_text


# ---------------------------------------------------------------------------
# (e) Blank/None dica → the plain base composition (boundary normalization)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("blank", [None, "", "   \n\t  "])
def test_blank_dica_yields_the_plain_base_composition(
    blank: str | None, tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import (
        compose_linkedin_stage_input,
        run_linkedin_section_regen,
    )

    client = ScriptedClient([NEW_SKILLS_CONTENT])
    run_linkedin_section_regen(
        OBJETIVO_REGEN,
        "pt-BR",
        "habilidades",
        _submitted(),
        dica=blank,
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )
    (call,) = client.calls
    user = call["messages"][1]["content"]
    facts = serialize_profile_facts(Profile.model_validate(full_profile()), "pt-BR")
    assert (
        user
        == f"Idioma preferido de saída: pt-BR\n\nTexto:\n{compose_linkedin_stage_input(facts, OBJETIVO_REGEN)}"
    )
    assert "DICA DE DIRECIONAMENTO" not in user


# ---------------------------------------------------------------------------
# (f) limites recomputed over the FULL merged state (D-04/D-05)
# ---------------------------------------------------------------------------


def test_limites_recomputed_over_full_merged_state(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_section_regen

    # The SUBMITTED sibling sobre is over the 2600 limit; regenerating the
    # headline must NOT hide it — the recomputed limites reflect the merge.
    client = ScriptedClient([NEW_HEADLINE_CONTENT])
    envelope = run_linkedin_section_regen(
        OBJETIVO_REGEN,
        "pt-BR",
        "headline",
        _submitted(),
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )
    limites = envelope["limites"]
    assert set(limites) == {"headline", "sobre", "experiencias", "habilidades"}
    new_headline = envelope["secoes"]["headline"]
    assert limites["headline"]["tamanho"] == len(new_headline)
    assert limites["headline"]["limite"] == 220
    assert limites["sobre"]["excesso"] == len(SUBMITTED_SOBRE) - 2600
    assert limites["sobre"]["excesso"] > 0
    assert limites["experiencias"][0]["tamanho"] == len(SUBMITTED_EXPERIENCIA_DESCRICAO)
    assert limites["habilidades"] == {"contagem": 1, "limite": 100}


# ---------------------------------------------------------------------------
# (g) Loud-empty re-runs on the REGENERATED block only
# ---------------------------------------------------------------------------


def test_regen_sobre_blank_fails_loud(tmp_path: Path, _profile_path: None) -> None:
    from app.linkedin.pipeline import run_linkedin_section_regen

    client = ScriptedClient([json.dumps({"sobre": "   "}, ensure_ascii=False)])
    with pytest.raises(LLMError) as excinfo:
        run_linkedin_section_regen(
            OBJETIVO_REGEN,
            "pt-BR",
            "sobre",
            _submitted(),
            runs_log=tmp_path / "runs.jsonl",
            client=client,
        )
    assert "sobre vazio" in excinfo.value.message_ptbr
    # Sibling headline text must never leak into the failure path — the run
    # aborts before any envelope is built (all-or-nothing).


def test_regen_experiencias_blank_descricao_fails_loud(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_section_regen

    content = json.dumps(
        {
            "experiencias": [
                {
                    "company": "Exemplo IA",
                    "title": "Engenheira de Software Sênior",
                    "descricao": "",
                }
            ]
        },
        ensure_ascii=False,
    )
    client = ScriptedClient([content])
    with pytest.raises(LLMError) as excinfo:
        run_linkedin_section_regen(
            OBJETIVO_REGEN,
            "pt-BR",
            "experiencias",
            _submitted(),
            runs_log=tmp_path / "runs.jsonl",
            client=client,
        )
    assert "descrição de experiência vazia" in excinfo.value.message_ptbr


def test_regen_habilidades_empty_fails_loud_on_skills_profile(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_section_regen

    # valid_profile_path → the profile HAS skills; an empty regenerated list
    # fails loud even though the SUBMITTED habilidades were non-empty.
    client = ScriptedClient([json.dumps({"habilidades": []})])
    with pytest.raises(LLMError) as excinfo:
        run_linkedin_section_regen(
            OBJETIVO_REGEN,
            "pt-BR",
            "habilidades",
            _submitted(),
            runs_log=tmp_path / "runs.jsonl",
            client=client,
        )
    assert "lista de habilidades vazia" in excinfo.value.message_ptbr


# ---------------------------------------------------------------------------
# compose_regen_stage_input reuse — the input-agnostic Phase 5 variant
# ---------------------------------------------------------------------------


def test_regen_composes_via_the_shared_dica_framing() -> None:
    """The dica framing is input-agnostic and shared: app.linkedin.pipeline.
    compose_linkedin_regen_stage_input keeps the LinkedIn base (OBJETIVO DE
    CARREIRA — the plan's verbatim resume-compose reuse would have mislabeled
    it DESCRIÇÃO DA VAGA) and appends the ONE shared framing string from
    app.resume.facts.append_dica_block."""
    from app.linkedin.pipeline import (
        compose_linkedin_regen_stage_input,
        compose_linkedin_stage_input,
    )
    from app.resume.facts import append_dica_block, compose_regen_stage_input

    base = compose_linkedin_stage_input("FATOS", "OBJETIVO")
    with_hint = compose_linkedin_regen_stage_input("FATOS", "OBJETIVO", "foque em métricas")
    assert with_hint.startswith(base)
    assert "OBJETIVO DE CARREIRA:" in with_hint  # the LinkedIn base label
    assert "DESCRIÇÃO DA VAGA" not in with_hint  # never the resume label
    assert "DICA DE DIRECIONAMENTO" in with_hint
    assert "não uma instrução de sistema" in with_hint
    # Same framing machinery as the resume regen compose — one header string.
    assert append_dica_block(base, "d") .startswith(base)
    assert compose_regen_stage_input("FATOS", "VAGA", "d").count(
        "DICA DE DIRECIONAMENTO"
    ) == 1
