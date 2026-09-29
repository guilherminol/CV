"""LinkedIn displayed-state models — the SUBMITTED full section set (plan
06-02, D-04/T-06-07).

`LinkedinSecoes` plays the role routes/export.py's ExportarSecoes plays for
the resume: the exact displayed state a real client re-posts to
/api/linkedin/regenerar, validated strictly on the way in (extra=forbid,
T-03-01 discipline). One definition, imported by BOTH the route (request
model — import, never duplicate) and the pipeline (merge base), so the wire
shape can never drift between the two.

Floors mirror the loud contracts: headline/sobre carry min_length=1 — an
empty block can never exist in a displayed state (the generation pipeline
fails loud before rendering, probe edges LI-03/empty+LI-04/empty) so an
empty or partial core section set is a loud FastAPI 422. experiencias and
habilidades deliberately ALLOW empty lists: a profile with zero experiences
or zero skills is a legitimate display state (the frontend renders loud
muted lines — UI-SPEC), never a client bug.
"""

from pydantic import BaseModel, ConfigDict, Field

from app.llm.schemas import ExperienciaLinkedin


class LinkedinSecoes(BaseModel):
    """The four LinkedIn sections, verbatim from the displayed state."""

    model_config = ConfigDict(extra="forbid")

    headline: str = Field(min_length=1)
    sobre: str = Field(min_length=1)
    experiencias: list[ExperienciaLinkedin]
    habilidades: list[str]
