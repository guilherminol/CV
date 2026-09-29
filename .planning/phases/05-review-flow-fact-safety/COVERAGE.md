# Phase 5 — API Coverage

No external API integration: Phase 5 reuses the existing OpenRouter gateway (`run_stage` + `_STAGE_SCHEMAS`, shipped Phase 2) via the internal `POST /api/resume/regenerar` route — zero new packages, zero new external endpoints (api-coverage probe: detected=false).
