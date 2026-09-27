# Phase 4: PDF Export + ATS Self-Check - Context

**Gathered:** 2026-09-27
**Status:** Ready for planning

<domain>
## Phase Boundary

O usuário exporta o currículo como PDF Google single-column genuinamente enviável: a montagem exibida na tela de resultado (D-05 Fase 3 — seções geradas + passthrough do perfil) é renderizada server-side para um PDF de camada de texto limpa e selecionável (REVIEW-02). Um gate automatizado de parse-back roda em todo export: extrai o texto do PDF e prova ordem de leitura (contato primeiro, títulos canônicos), coocorrência empresa+cargo+datas por experiência e acentos PT-BR intactos — nos dois idiomas. Na sequência, o self-check ATS roda na interface e mostra a verificação de ordem de seções e sobrevivência de keywords sobre o texto extraído do PDF exportado, nos dois idiomas (REVIEW-03).

Not in this phase: regenerar seção individual, edição inline, diff fato-vs-gerado e política de write-back (Fase 5); LinkedIn (Fase 6); glossário/QA gate de PT-BR (Fase 6). Sem score numérico de ATS (REQUIREMENTS Out of Scope).

</domain>

<decisions>
## Implementation Decisions

### Motor de renderização do PDF
- **D-01:** **Playwright** (Chromium headless, print-to-PDF) como motor de renderização — fidelidade ao layout revisado no app via print CSS; controle total do texto no template. `window.print()` client-side foi rejeitado: o gate de parse-back não seria automatizável. — **Reversibility:** reversible — o template HTML server-side é motor-agnóstico; WeasyPrint consome o mesmo HTML.
- **D-02:** **Decisão Playwright vs WeasyPrint é empírica** — construir o gate de parse-back primeiro, testar ambos os motores contra ele, embarcar o que passar (preocupação registrada no STATE.md; WeasyPrint é o fallback pré-aprovado). Se ambos passarem, Playwright embarca (fidelidade de layout).
- **D-03:** **Template HTML dedicado server-side (Python)** espelhando a montagem D-05 da tela de resultado — única fonte de verdade do layout de export, motor-agnóstico, funciona para Playwright e WeasyPrint. reportlab texto puro rejeitado: perderia a fidelidade visual do formato Google.
- **D-04:** **Playwright pinado em dev-deps + `playwright install chromium` como passo de setup documentado** no README/backend. (Se WeasyPrint vencer o gate, a dependência de browser é dispensada.)

### Gate de parse-back (REVIEW-03)
- **D-05:** **pypdf** como extrator de texto do gate — Python puro, leve, prova exatamente o que importa: a camada de texto existe e é extraível em ordem.
- **D-06:** **Checagens completas da SC2:** ordem de leitura (contato primeiro, títulos canônicos na ordem esperada), coocorrência empresa+cargo+datas por experiência, acentos PT-BR intactos — verificado em exports PT-BR e EN.
- **D-07:** **Gate automático em todo export, server-side** — faz parte do endpoint de export (SC2: "passes on every export"), não depende de ação ou disciplina do usuário.
- **D-08:** **Falha do gate = falha alta:** export rejeitado, mensagem PT-BR nomeando a verificação que falhou, raw detail só no terminal (filosofia fail-fast das Fases 1–2, D-13/D-14). PDF com defeito nunca chega ao usuário como se estivesse bom.

### Fluxo de exportação (UX)
- **D-09:** **CTA primário na tela de resultado**, abaixo do currículo montado — "Exportar PDF".
- **D-10:** **Exporta exatamente o estado montado exibido no app** (seções geradas + passthrough) — SC1 "matches what was reviewed in-app". Regenerar server-side a partir do perfil rejeitado: não seria o que o usuário revisou.
- **D-11:** **Endpoint POST retorna os bytes do PDF → download no browser**, nome convencional `curriculo-{idioma}-{data}.pdf`.
- **D-12:** **Idioma do PDF segue automaticamente o idioma da execução** — sem seletor extra no export.

### Self-check ATS na interface (REVIEW-03 UX)
- **D-13:** **Self-check roda automaticamente logo após o export bem-sucedido** (mesma resposta do endpoint) — sem botão separado.
- **D-14:** **Painel na tela de resultado:** ordem das seções ✓/✗ + sobrevivência de keywords sobre o texto extraído do PDF.
- **D-15:** **Sobrevivência de keywords reusa o matcher determinístico da Fase 3** (canônico+alias, D-02/D-11) sobre o texto extraído do PDF, por idioma — checklist honesto e auditável. Julgamento por LLM rejeitado: precisão falsa (REQUIREMENTS exclui score ATS) e custo.
- **D-16:** **Resultados efêmeros, na sessão** (coerente com D-06 Fase 3).

### Claude's Discretion
- Mecânica exata do Playwright no backend (síncrono em threadpool vs subprocess), versionamento do browser, template engine (string/HTML direto recomendado — sem engine de template nova se dispensável).
- Detalhes das checagens do gate (tolerância de whitespace, normalização de acentos na comparação), mensagens PT-BR exatas de cada falha.
- Estrutura do módulo backend (ex.: `app/export/`), contrato exato do endpoint (multipart vs bytes diretos), headers de download.
- Componentes React do painel de self-check, reuso de StatusLine/chips existentes, strings em `constants/ui.ts`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — constraints (localhost, JS frontend/Python backend, PDF Google single-column como único output), Out of Scope (sem score ATS numérico)
- `.planning/REQUIREMENTS.md` — REVIEW-02 e REVIEW-03 (esta fase); RESUME-04 (matcher de cobertura que o self-check reusa)
- `.planning/ROADMAP.md` §Phase 4 — goal + 3 success criteria (a barra de aceitação)

### Prior phase decisions this phase builds on
- `.planning/phases/03-resume-vertical-slice/03-CONTEXT.md` — D-05 (montagem do resultado = o que o PDF renderiza), D-06 (conteúdo efêmero), D-02 (matcher determinístico canônico+alias do checklist de cobertura)
- `.planning/phases/01-foundation-scaffold-master-profile/01-CONTEXT.md` — D-12 (ProfilePreview estabelece o layout estilo-currículo), D-13/D-14 (erros PT-BR, raw detail só no terminal)

### Research / STATE
- `.planning/STATE.md` §Blockers/Concerns — "Phase 4: resolve Playwright vs WeasyPrint empirically via the parse-back gate (WeasyPrint is the pre-approved fallback)" → resolvido por D-02

No external specs/ADRs — no user-referenced docs beyond the planning set above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/ResumeResult.tsx` — a montagem D-05 (geradas + passthrough, badges, `tLang()` run-language) que o template de impressão espelha
- `frontend/src/components/ProfilePreview.tsx` — layout estilo-currículo e ordem visual de referência para o template de impressão
- `backend/app/resume/coverage.py` — matcher determinístico (canônico+alias, fold/lookaround) a reusar na checagem de sobrevivência de keywords sobre o texto do PDF
- `backend/app/routes/resume.py` — padrão envelope 200+status (nunca 500, raw detail só no terminal), sync `def` para operações bloqueantes (threadpool — aplica-se ao Playwright)
- `frontend/src/api/client.ts` — client tipado; `tsc -b` trava drift Pydantic↔TS (blob download precisará de manuseio binário)
- `frontend/src/constants/ui.ts` — strings PT-BR centralizadas

### Established Patterns
- Falha alta: mensagem PT-BR ao usuário + raw detail só no terminal (Fase 1 D-13/D-14)
- Sem cache — re-leitura fresca por request
- Rotas registradas ANTES do mount SPA em `main.py` (Pitfall 5)
- Pydantic estrito `extra="forbid"` em todo request model
- Testes 100% offline por padrão; rede/LLM só sob `pytest -m llm` (o gate de parse-back é offline por natureza — fixture de PDF gerado em teste)
- React Query v5, Tailwind, layout `max-w-3xl`

### Integration Points
- `backend/app/main.py` — novo router de export antes do mount SPA
- Novo módulo backend de export (render HTML → PDF → gate) — consumo direto do payload de seções que a tela já monta
- `logs/runs.jsonl` — export não é chamada LLM; sem linha nova (contrato D-13 Fase 2 preservado)
- Tela de resultado (`CurriculoHome`/`ResumeResult`) — botão Exportar + painel de self-check como novos blocos

</code_context>

<specifics>
## Specific Ideas

- O PDF precisa ser "genuinamente enviável" — o gate de parse-back é a materialização disso: o app só entrega um PDF que ele mesmo provou ser parseável, nos dois idiomas.
- Coerência com a filosofia do projeto: gate automático (não depende de disciplina), falha alta (PDF ruim nunca passa), honestidade mecânica (matcher auditável, sem score numérico).
- A preocupação do STATE.md (Playwright vs WeasyPrint) foi resolvida como decisão empírica com fallback pré-aprovado — o planner deve sequenciar o gate antes da escolha final do motor.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-PDF Export + ATS Self-Check*
*Context gathered: 2026-09-27*
