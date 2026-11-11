"""Profile updater — add extracted JD keywords to the profile data (vaga → perfil).

Pure meta-dict mutation: the route owns ALL I/O (read frontmatter → mutate
HERE → validate → write). The caller passes the raw frontmatter metadata dict
and a list of keyword additions; the return reports what was added and what
was already present.

Stored value convention: the base-language (pt-BR) rendering — skill items
are single-value plain names (D-09), and the EN rendering of generated
sections happens at generation time (resume-skills language rule). Proper
nouns/product names carry pt == en, so the choice is invisible for them.

Dedup: whitespace-normalized casefold within the destination section. One
skill must never live twice in the profile; an accent-insensitive norm is
deliberate (extracted keywords and profile items come from the same
canonical family — "Kubernetes" never collides with "kubernetes " noise).
"""

from typing import Literal

CategoriaDestino = Literal["competencias", "ferramentas", "certificacoes"]

# Keyword category → profile skills group. Groups are created on first add —
# the owner consolidates categories by hand in profile.md if desired.
SKILL_CATEGORY_MAP: dict[str, str] = {
    "ferramentas": "Ferramentas",
    "competencias": "Competências",
}


def _norm(name: str) -> str:
    """Dedup key: collapse whitespace runs + casefold (accent-sensitive by design)."""
    return " ".join(name.split()).casefold()


class AdicaoKeyword:
    """One keyword the user accepted into their profile (mirrors the route DTO).

    A plain class (not Pydantic) keeps this module framework-free — the route
    parses the request, this module only needs the four values.
    """

    __slots__ = ("canonical", "pt", "en", "categoria")

    def __init__(self, canonical: str, pt: str | None, en: str | None, categoria: str):
        self.canonical = canonical
        self.pt = pt
        self.en = en
        self.categoria = categoria


def _stored_name(adicao: AdicaoKeyword) -> str:
    """pt-BR rendering with canonical fallback — the base-language convention."""
    return (adicao.pt or adicao.canonical).strip()


def add_keywords_to_meta(
    meta: dict, adicoes: list[AdicaoKeyword]
) -> tuple[list[str], list[str]]:
    """Mutate the profile metadata dict in place, adding each accepted keyword.

    Returns (adicionado, ja_existentes) — stored names, in request order.
    Certifications land as name-only entries (issuer/year stay for the owner
    to complete by hand in profile.md); titles have no profile home and are
    rejected upstream by the route's request model.
    """
    skills = meta.setdefault("skills", [])
    certifications = meta.setdefault("certifications", [])

    known_skills = {
        _norm(item) for group in skills for item in group.get("items", [])
    }
    known_certs = {_norm(cert.get("name", "")) for cert in certifications}

    adicionado: list[str] = []
    ja_existentes: list[str] = []

    for adicao in adicoes:
        nome = _stored_name(adicao)
        if not nome:
            continue
        if adicao.categoria == "certificacoes":
            if _norm(nome) in known_certs or _norm(adicao.canonical) in known_certs:
                ja_existentes.append(nome)
                continue
            certifications.append({"name": nome})
            known_certs.add(_norm(nome))
        else:
            categoria = SKILL_CATEGORY_MAP[adicao.categoria]
            if _norm(nome) in known_skills or _norm(adicao.canonical) in known_skills:
                ja_existentes.append(nome)
                continue
            group = next((g for g in skills if g.get("category") == categoria), None)
            if group is None:
                group = {"category": categoria, "items": []}
                skills.append(group)
            group["items"].append(nome)
            known_skills.add(_norm(nome))
        adicionado.append(nome)

    return adicionado, ja_existentes
