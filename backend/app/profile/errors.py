"""PT-BR error localization (D-14).

Maps the exactly five Pydantic error types Phase 1 can produce (verified
empirically — RESEARCH Pattern 3) to PT-BR phrases, and renders loc tuples as
D-14-style paths ("experiences[2].data_fim"). Raw ValidationError detail never
reaches the UI/API path — it goes to the uvicorn terminal log only (D-13;
threat T-01-07 mitigation).
"""

from pathlib import Path

from pydantic import ValidationError

# The five producible error types. value_error carries the validator's own
# message, which is already PT-BR (the base-language mixin) — so None means
# "pass the original msg through".
_PTBR_BY_TYPE = {
    "missing": "campo obrigatório ausente",
    "extra_forbidden": "chave desconhecida — provável erro de digitação (chaves extras não são aceitas)",
    "string_type": "texto esperado, encontrado valor de outro tipo",
    "literal_error": "valor fora das opções permitidas",
    "value_error": None,
}


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
        msg = _PTBR_BY_TYPE.get(e["type"], e["msg"])
        lines.append(f"  • {render_loc(e['loc'])} — {msg or e['msg']}")
    return "\n".join(lines)
