"""HTML → PDF engine seam (D-01/D-02/D-04) — THE ONLY playwright import in the backend.

render.py (template) and gate.py (parse-back) import no browser machinery:
the whole engine choice lives behind html_to_pdf, so WeasyPrint remains a
one-function swap (D-02's pre-approved fallback) and the empirical gate
verdict can be re-run against any candidate engine unchanged.

Mechanics (research Pattern 2, probe-verified 2026-09-27 on this machine):
SYNC Playwright on the calling thread — the export route is a plain `def`
(Starlette threadpool: no running asyncio loop there; async def +
sync_playwright raises RuntimeError). Per-request launch + close in `finally`
— no module-level cached browser (the anyio pool hands a different thread to
each request and sync Playwright has per-thread state assumptions). ~0.9s
launch per export is the documented cost (threat T-04-06: accepted for a
localhost single-user tool). No asyncio anywhere in this module.

Version pin (Pitfall 2): playwright==1.62.0 bundles chromium-1234 — the
revision already cached in %LOCALAPPDATA%\\ms-playwright on the maintainer
machine. A mismatched cache is invisible until launch, so launch/lookup
failures raise ExportError with the PT-BR install hint (Pitfall 4) and raw
detail terminal-only (D-08).
"""

from playwright.sync_api import sync_playwright

from app.export.errors import ExportError

_BROWSER_MISSING_PTBR = (
    "O navegador de renderização não está instalado. "
    "Execute `uv run playwright install chromium` e tente novamente."
)

# IN-01: render-stage failures (set_content timeout, page.pdf() error) are NOT
# fixed by installing a browser — blaming the install misleads the user. The
# generic retry hint keeps the fail-loud PT-BR envelope honest; the raw detail
# stays terminal-only (D-08).
_RENDER_FALHOU_PTBR = (
    "Falha ao renderizar o PDF. Tente novamente — o detalhe técnico completo "
    "aparece no terminal onde o servidor está rodando."
)


def html_to_pdf(html: str) -> bytes:
    """Render a complete HTML document to A4 PDF bytes via headless Chromium.

    print_background keeps section rules/colors; prefer_css_page_size lets the
    template's @page rule win (A4, 1.6cm margins); tagged=True emits a
    tagged/accessible PDF — real heading structure helps some ATS parsers
    (probe A4: real embedded text layer, accents byte-perfect).

    The failure STAGE picks the PT-BR line (IN-01): launch/executable-lookup
    failures carry the Chromium install hint (the actionable remediation);
    every other failure — render, driver startup — carries the generic retry
    hint, because `playwright install` will not fix it. Raw detail goes to
    the terminal in BOTH branches, never the envelope (D-08).
    """
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:  # browser missing / executable lookup (Pitfall 4)
                raise ExportError(
                    _BROWSER_MISSING_PTBR, f"{type(exc).__name__}: {exc}"
                ) from exc
            try:
                page = browser.new_page()
                page.set_content(html, wait_until="load")
                return page.pdf(
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    tagged=True,
                )
            except Exception as exc:  # render-stage failure (IN-01) — install won't help
                raise ExportError(
                    _RENDER_FALHOU_PTBR, f"{type(exc).__name__}: {exc}"
                ) from exc
            finally:
                browser.close()
    except ExportError:
        raise
    except Exception as exc:  # driver/playwright startup — generic hint (IN-01)
        raise ExportError(_RENDER_FALHOU_PTBR, f"{type(exc).__name__}: {exc}") from exc
