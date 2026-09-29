"""Resume orchestration — one function per API surface (RESUME-01/02/04, PROFILE-02).

`run_lint_only` powers POST /api/resume/lint (pre-generate keyword extraction +
JD-tied lint, SC5); `run_resume_pipeline` powers POST /api/resume/gerar —
extraction → lint → the three section stages SEQUENTIALLY in D-01 order
(resume-summary → resume-experiencias → resume-skills) → deterministic
coverage over the GENERATED text only (Pitfall 7) — all through the Phase 2
gateway (`run_stage`), so retry/validation/runs.jsonl audit are inherited
(D-13). `run_section_regen` powers POST /api/resume/regenerar (plan 05-01):
exactly ONE stage — SECTION_STAGE_BY_ID[section]'s own — merged server-side
over the SUBMITTED displayed state with siblings byte-identical (D-06/D-07).

House disciplines carried here:
- ALL-OR-NOTHING: exceptions propagate UNTOUCHED — the ROUTE owns the erro
  envelope. A raised LLMError aborts before any envelope dict is built, so a
  partial section set is structurally unreachable (T-03-07).
- No caching: load_profile() runs fresh ONCE per invocation (D-15) and the
  facts are passed down — no memoization anywhere.
- `runs_log` and `client` thread through to EVERY run_stage call: the
  injection seam that keeps the default suite offline (D-16).

Keyword extraction language is fixed ("pt-BR") in BOTH paths — the extraction
stage always produces the bilingual {pt, en} map (D-09/D-11); run-language
selection happens at matching time (coverage/lint primitives, plan 03-02).
The lint endpoint's keywords are for DISPLAY pre-generate; the gerar response
echoes ITS OWN extraction verbatim (research anti-pattern "trusting the
client").
"""

from pathlib import Path

from app.llm.gateway import run_stage
from app.llm.schemas import Keyword
from app.profile.loader import load_profile
from app.resume.coverage import classify_coverage, summarize_coverage
from app.resume.facts import compose_regen_stage_input, compose_stage_input, serialize_profile_facts
from app.resume.lint import lint_jd_tied
from app.routes.export import ExportarSecoes

EXTRACTION_STAGE = "keyword-extraction"
SECTION_STAGES = ("resume-summary", "resume-experiencias", "resume-skills")  # D-01

# Phase 5 (plan 05-01): section id → gateway stage, built FROM SECTION_STAGES
# order (D-06: regeneration = the section's own run_stage via the existing
# gateway; extraction and sibling stages never run).
SECTION_STAGE_BY_ID = {
    "resumo": SECTION_STAGES[0],
    "experiencias": SECTION_STAGES[1],
    "habilidades": SECTION_STAGES[2],
}


def run_lint_only(
    jd_text: str,
    runs_log: Path | None = None,
    client: object | None = None,
) -> dict:
    """Extraction + JD-tied lint for the pre-generate display (SC5).

    Returns {"keywords": [keyword dicts], "avisos": [PT-BR strings]} —
    non-blocking avisos per D-03; failures raise (ProfileError from the
    loader, LLMError from the gateway) and belong to the route's envelope.
    """
    extraction = run_stage(
        EXTRACTION_STAGE, jd_text, "pt-BR", runs_log=runs_log, client=client
    )
    keywords = extraction.keywords
    avisos = lint_jd_tied(load_profile(), keywords)
    return {
        "keywords": [keyword.model_dump() for keyword in keywords],
        "avisos": avisos,
    }


def run_resume_pipeline(
    jd_text: str,
    language: str,
    runs_log: Path | None = None,
    client: object | None = None,
) -> dict:
    """One call: extraction → lint → 3 sequential section stages → coverage.

    Returns the ok envelope of the normative API contract (plan 03-03): the
    gerar response's keywords/cobertura come from THIS call's own extraction —
    never from a prior lint call. Raises on any stage failure; the route
    converts to the erro envelope (all-or-nothing, T-03-07).
    """
    profile = load_profile()  # fresh, once per invocation (D-15) — passed down
    facts = serialize_profile_facts(profile, language)
    stage_input = compose_stage_input(facts, jd_text)

    extraction = run_stage(
        EXTRACTION_STAGE, jd_text, "pt-BR", runs_log=runs_log, client=client
    )
    keywords = extraction.keywords
    avisos = lint_jd_tied(profile, keywords)

    # D-01 order, sequential — each section stage gets the SAME composed blob.
    summary = run_stage(
        SECTION_STAGES[0], stage_input, language, runs_log=runs_log, client=client
    )
    experiencias = run_stage(
        SECTION_STAGES[1], stage_input, language, runs_log=runs_log, client=client
    )
    skills = run_stage(
        SECTION_STAGES[2], stage_input, language, runs_log=runs_log, client=client
    )

    secoes = {
        "resumo": summary.resumo,
        "experiencias": [entry.model_dump() for entry in experiencias.experiencias],
        "habilidades": list(skills.habilidades),
    }
    # Coverage input is the GENERATED sections' text ONLY — never profile
    # passthrough content, never the other language's renderings (Pitfall 7).
    generated_text = "\n".join(
        [summary.resumo]
        + [bullet for entry in experiencias.experiencias for bullet in entry.bullets]
        + list(skills.habilidades)
    )
    cobertura = classify_coverage(keywords, generated_text, language)
    return {
        "status": "ok",
        "idioma": language,
        "keywords": [keyword.model_dump() for keyword in keywords],
        "avisos": avisos,
        "secoes": secoes,
        "cobertura": cobertura,
        "cobertura_resumo": summarize_coverage(cobertura),
    }


def run_section_regen(
    jd_text: str,
    language: str,
    secao: str,
    secoes: ExportarSecoes,
    keywords: list[Keyword],
    dica: str | None = None,
    runs_log: Path | None = None,
    client: object | None = None,
) -> dict:
    """Regenerate ONE section: exactly ONE gateway stage → server-side merge
    over the SUBMITTED displayed state → coverage over the merged text
    (plan 05-01, SC1/D-06/D-07).

    Returns the ok envelope {status, idioma, secoes, cobertura,
    cobertura_resumo}: `secoes` is the FULL merged section set — the target
    section replaced by the stage output, every sibling byte-identical to the
    submitted value (SC1 is a response-level property, so the frontend
    replaces its state wholesale with no client-side merge). Raises on any
    failure; the route converts to the erro envelope (all-or-nothing).
    """
    profile = load_profile()  # fresh, once per invocation (D-15) — passed down
    facts = serialize_profile_facts(profile, language)
    # Blank/None dica normalizes to the plain base composition (compose
    # boundary — Pitfall 5); a real dica travels as user-message DATA only.
    stage_input = compose_regen_stage_input(facts, jd_text, dica)

    # Exactly ONE stage for the requested section (D-06) — run_stage returns
    # the output already validated against that stage's strict schema.
    output = run_stage(
        SECTION_STAGE_BY_ID[secao], stage_input, language, runs_log=runs_log, client=client
    )

    # Siblings pass through BY REFERENCE from the submitted state — never
    # re-rendered, reordered, or re-generated (D-07/SC1, pinned by identity
    # assertions in tests/test_resume_regen_pipeline.py).
    merged = {
        "resumo": secoes.resumo,
        "experiencias": [entry.model_dump() for entry in secoes.experiencias],
        "habilidades": list(secoes.habilidades),
    }
    if secao == "resumo":
        merged["resumo"] = output.resumo
    elif secao == "experiencias":
        merged["experiencias"] = [entry.model_dump() for entry in output.experiencias]
    else:
        merged["habilidades"] = list(output.habilidades)

    # Coverage input is the FULL merged generated text — exactly the input
    # run_resume_pipeline assembles from its three sections (Pitfall 7).
    generated_text = "\n".join(
        [merged["resumo"]]
        + [bullet for entry in merged["experiencias"] for bullet in entry["bullets"]]
        + list(merged["habilidades"])
    )
    cobertura = classify_coverage(keywords, generated_text, language)
    return {
        "status": "ok",
        "idioma": language,
        "secoes": merged,
        "cobertura": cobertura,
        "cobertura_resumo": summarize_coverage(cobertura),
    }
