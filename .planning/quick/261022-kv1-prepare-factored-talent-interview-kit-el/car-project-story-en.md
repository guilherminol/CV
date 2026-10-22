# CAR Project Story — Group Verifica (Factored Talent Interview, English)

- **Project:** Group Verifica (Group Software) — criminal-background and lawsuit analysis for the condominium and HR markets
- **Total target:** 3 minutes (email target; matches the deck's CAR timing: 30s + 1.5min + 1min)
- **Total script:** 418 words
- **Per-section timing at 130–150 wpm:** Context 78 words ≈ 33s · Action 206 words ≈ 1:28 · Result 134 words ≈ 55s — rehearse to land at ~3:00
- **Why this project:** direct "I" ownership (built end to end), hard results in all three Result currencies the deck names (revenue, users, time/cost), and a production generative-AI product — Factored's space.

<!-- context-script-start -->
Group Software builds software for the condominium and HR markets. In both, screening people, whether criminal records or lawsuits, was a manual process: one analysis took nearly a full analyst day. Our clients, condominium administrators and HR teams, were losing days on every decision. I work in a highly autonomous agile squad in constant contact with the product side, so the bottleneck was visible to everyone. I kept progress visible through our squad rituals and close product alignment.
<!-- context-script-end -->

<!-- action-script-start -->
My main responsibility was building the entire solution end to end: frontend, backend, AI, and database. I designed the core as LangGraph agent flows with tools that query real-time background-check APIs, so every analysis works on live data.

At the heart of the product, I built a configurable risk engine with three risk levels: Brando, Normal, and Rigoroso. Each client chooses how strict the screening should be. Every decision the engine makes is fully traceable, and that was deliberate: background screening affects people's opportunities, so our clients need to explain why a candidate was flagged. I also implemented fallback logic, because external APIs can fail or return partial data, and the analysis still has to complete.

A large part of the work was integration: connecting the product to legacy systems and production databases without disrupting what was already running.

On deadlines and priorities, launch was the driver: the product shipped with generative AI and reached 53 tested clients within 20 days of launch, so we protected a thin, complete slice over broad features. My key initiatives were structural: owning the stack end to end, making the risk levels configurable instead of hardcoded, and enforcing decision traceability from day one, because those choices made every result defensible.
<!-- action-script-end -->

<!-- result-script-start -->
The results validated the approach on three fronts.

Time: an analysis that took an analyst nearly a full manual day now completes in under 30 seconds, a ~90% reduction in analysis time.

Revenue: the product reached R$4,750 in monthly recurring revenue within its first 45 days.

Demand: 53 clients tested the product within the first 20 days, and 72% of them demonstrated purchase interest, independent evidence that the problem was real and the solution fit. In production, the platform has processed more than 196 queries.

So the business impact is the pattern I look for in every AI project: a hard operational cost collapsed, a new revenue line opened, and real customers validated demand with their intent to buy. These are live production numbers, not projections, and they are why I trust this pattern.
<!-- result-script-end -->

## Rehearsal annotations

### Pause marks

**Context:**
- Pause after **"…condominium and HR markets."** — setup done; let the market context settle.
- Pause after **"…nearly a full analyst day."** — the problem has landed; this is the pain point, give it air.
- Short breath before **"I kept progress visible…"** — shift into your own working style.

**Action:**
- Pause after **"…works on live data."** — end of the responsibility headline.
- Pause after **"…Normal, and Rigoroso."** — let the three levels register.
- Pause after **"…why a candidate was flagged."** — that is the "why traceability" moment; it shows product judgment.
- Breath before **"On deadlines and priorities…"** — signals you're answering the deck's fourth Action bullet.

**Result:**
- Pause after **"…on three fronts."** — then deliver one front per breath.
- One beat of silence after each number: **30 seconds**, **~90%**, **R$4,750**, **45 days**, **53**, **20 days**, **72%**, **196**. This interviewer rewards numbers; don't bury them.
- Long pause before the closing sentence — then finish calm, eye contact with the camera.

### Deck checklist coverage

Business problem ✓ (manual screening, ~1 analyst day) · situation ✓ (Group Software ships for these markets and saw the bottleneck) · stakeholders ✓ (condominium administrators and HR teams — the product's clients — plus my own autonomous squad) · communication of progress ✓ (squad rituals, close product alignment, autonomous squad).

### Anticipated follow-up questions

**Follow-up 1 — "Why three risk levels?"**
> Different clients tolerate different levels of risk, so I made the strictness configurable instead of hardcoding one policy. The three levels — Brando, Normal, and Rigoroso — let each client calibrate screening to their own context. And whatever level a client picks, every decision stays fully traceable, so they can always explain a flag.

*Grounding: profile — "Engine configurable in 3 risk levels (Brando/Normal/Rigoroso) with fallback logic and full traceability of every decision."*

**Follow-up 2 — "What was the hardest part? Did anything go wrong?"**
> The hardest part was integration: the product had to connect to legacy systems and production databases, and the background-check APIs are external, so they can fail or return partial data. I implemented fallback logic so an analysis still completes when an API misbehaves, with full traceability of every decision so we can audit exactly what happened. I wouldn't call anything a failure — those constraints shaped the architecture from the start.

*Grounding: profile — "Integration with legacy systems and production databases"; "fallback logic"; "full traceability of every decision." (No invented failure story — honest framing of real constraints.)*

**Follow-up 3 — "Can you share another project?"**
> Yes — a 20-second version: I also implemented the AI meeting-minutes feature at Group Software. It generated 482 meeting minutes in 49 days of production, reached 68.1% organic adoption with no push, and eliminated 1,446 specialist hours, with 135 management companies adopting it. Same through-line as Group Verifica: generative AI applied exactly where the business bleeds time.

*Grounding: profile — 482 minutes in 49 days; 68.1% organic adoption (peak 77.3%); 1,446 specialist hours eliminated; 135 management companies.*

**Follow-up 4 — "How did you handle the deadline?"**
> Launch was the hard constraint. Because I owned the stack end to end there were no handoff waits, and we prioritized a thin, complete slice of the product over breadth. The outcome shows the prioritization held: the product shipped with generative AI, and 53 clients tested it within the first 20 days.

*Grounding: profile — "Built the Group Verifica solution end to end (frontend, backend, AI, and database)"; "Product shipped with generative AI"; "53 clients tested within 20 days."*

### Timing check

Timing check: the three scripts total 418 words — rehearse toward ~420 total at ~140 wpm (≈2:56–3:00). If you run long, trim Action first, never Result.
