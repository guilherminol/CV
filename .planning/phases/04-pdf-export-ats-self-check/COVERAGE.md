# API Coverage — Phase 4: PDF Export + ATS Self-Check

No external API integration: the phase's only network-adjacent surface is the app's own FastAPI route (`POST /api/resume/exportar`, plans 04-02/04-03); the integrations are Python libraries (playwright 1.62.0 for Chromium print-to-PDF, pypdf >= 6.19.0 for text extraction), both pinned from 04-RESEARCH.md's legitimacy-audited stack.

The api-coverage detector's `detected: true` (run 2026-09-27 over the three PLAN bodies + the roadmap section) fired solely on the word "endpoint" in self-references to that internal route — no external API/SDK service is consumed, so per protocol this file is the reasoned declaration the verify:pre seal-time gate checks for.
