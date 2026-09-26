"""PT-BR error localization (D-14).

Maps the Pydantic error types the Phase 1 schema can produce (empirically
verified — RESEARCH Pattern 3 — and extended after review WR-01 proved that
model_type, dict_type, list_type, bool_type and bool_parsing also occur) to
PT-BR phrases, and renders loc tuples as D-14-style paths
("experiences[2].data_fim"). Raw ValidationError detail never reaches the
UI/API path — it goes to the uvicorn terminal log only (D-13; threat T-01-07
mitigation). Types outside the map fall back to a PT-BR template, never to
Pydantic's English prose.
"""

from pathlib import Path

from pydantic import ValidationError

# value_error carries the raising validator's own message, which Phase 1
# validators write in PT-BR (the base-language mixin, field validators) — it
# is passed through, not replaced by a map phrase.
_VALUE_ERROR_TYPE = "value_error"

# Every error type the Phase 1 schema can realistically produce.
_PTBR_BY_TYPE = {
    "missing": "campo obrigatório ausente",
    "extra_forbidden": "chave desconhecida — provável erro de digitação (chaves extras não são aceitas)",
    "string_type": "texto esperado, encontrado valor de outro tipo",
    "literal_error": "valor fora das opções permitidas",
    "model_type": "estrutura esperada (bloco de dados), encontrado valor simples",
    "dict_type": "dicionário esperado, encontrado valor de outro tipo",
    "list_type": "lista esperada, encontrado valor de outro tipo",
    "bool_type": "verdadeiro/falso esperado, encontrado valor de outro tipo",
    "bool_parsing": "verdadeiro/falso esperado, encontrado texto não reconhecido",
}

# Fallback for types outside the map (future Pydantic versions, exotic shapes):
# a PT-BR template instead of raw English (D-14). The full English detail
# remains available in ProfileError.raw — terminal only (D-13).
_UNKNOWN_TYPE_TEMPLATE = "valor inválido para este campo (verifique o tipo e o formato do valor)"


def _ptbr_message(error: dict) -> str:
    """PT-BR message for one entry of ValidationError.errors() — never English."""
    if error["type"] == _VALUE_ERROR_TYPE:
        return error["msg"]  # validator's own message — already PT-BR in Phase 1
    return _PTBR_BY_TYPE.get(error["type"], _UNKNOWN_TYPE_TEMPLATE)


def render_loc(loc: tuple) -> str:
    """Render a Pydantic loc tuple as a D-14 dotted/indexed path.

    - ints become [index] ("experiences[2]")
    - the literal "[key]" marker (literal_error on a dict key) becomes " (chave)"
    - the EMPTY loc of model_validator failures (Pitfall 8) renders as
      "estrutura do perfil"
    """
    out = ""
    for part in loc:
        if isinstance(part, int):
            out += f"[{part}]"
        elif part == "[key]":
            out += " (chave)"
        else:
            out += f"{'' if not out else '.'}{part}"
    return out or "estrutura do perfil"


def render_errors_ptbr(exc: ValidationError, path: Path) -> str:
    """Render every validation error as a 'Erro no perfil: {path}' + bullet lines."""
    lines = [f"Erro no perfil: {path}"]
    for e in exc.errors(include_url=False):
        lines.append(f"  • {render_loc(e['loc'])} — {_ptbr_message(e)}")
    return "\n".join(lines)
