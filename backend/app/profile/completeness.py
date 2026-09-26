"""Section completeness for the Perfil status home (D-12).

Presence + counts ONLY — explicitly NOT the PROFILE-02 completeness lint
(that is JD-tied and lands in Phase 3). Computed fresh per request alongside
the D-15 load; no caching anywhere.
"""

from app.profile.models import Profile


def compute_completude(profile: Profile) -> dict:
    """PT-BR-keyed map of section presence and counts for GET /api/profile."""
    return {
        "resumo": bool(profile.summary),
        "experiencias": bool(profile.experiences),
        "experiencias_qtde": len(profile.experiences),
        "experiencias_impactos_qtde": sum(len(e.impacts) for e in profile.experiences),
        "educacao": bool(profile.education),
        "educacao_qtde": len(profile.education),
        "habilidades": bool(profile.skills),
        "habilidades_qtde": len(profile.skills),
        "habilidades_itens_qtde": sum(len(g.items) for g in profile.skills),
        "certificacoes": bool(profile.certifications),
        "certificacoes_qtde": len(profile.certifications),
        "idiomas": bool(profile.languages),
        "idiomas_qtde": len(profile.languages),
        "projetos": bool(profile.projects),
        "projetos_qtde": len(profile.projects),
    }
