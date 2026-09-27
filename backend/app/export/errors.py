"""Export-layer errors (D-08) — exact LLMError shape (app/llm/errors.py:43-50).

`message_ptbr` is the envelope-safe PT-BR line (the only text that may reach
the user); `raw` is terminal-only technical detail. Gate failures carry the
same split inside GateResult — one fail-loud philosophy across the whole
export path (D-13/D-14 lineage).
"""


class ExportError(Exception):
    """Export pipeline failure (browser missing, render failure, extraction failure)."""

    def __init__(self, message_ptbr: str, raw: str):
        super().__init__(message_ptbr)
        self.message_ptbr = message_ptbr
        self.raw = raw  # terminal-only detail (D-08)
