# Multi-stage: frontend (Vite) + backend (FastAPI + Playwright/Chromium).
# O container final roda a MESMA estrutura de repo do dev (backend/app,
# content/, prompts/, frontend/dist) — app/config.py resolve REPO_ROOT via
# parents[2], então o layout nunca muda entre local e imagem.

# ---- 1. Build do SPA ----
FROM node:22-alpine AS web
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- 2. Runtime ----
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1

WORKDIR /srv/cv

# Deps primeiro (cache de layer só quebra quando o lock muda)
COPY backend/pyproject.toml backend/uv.lock backend/
RUN cd backend && uv sync --frozen --no-dev

# Chromium para o export de PDF (playwright==1.62.0, revisão pinada no lock)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN cd backend && uv run --no-dev playwright install --with-deps chromium

# Código + assets de conteúdo (content/ e logs/ são sombreados por bind mount
# no compose; a cópia na imagem é fallback para rodar sem mount)
COPY backend/ backend/
COPY content/ content/
COPY prompts/ prompts/
COPY --from=web /fe/dist frontend/dist

# Mesmo UID do dono dos bind mounts no host (guilhermino = 1000 no homelab)
RUN useradd --uid 1000 --create-home cv
USER cv

WORKDIR /srv/cv/backend
EXPOSE 8000
CMD ["/srv/cv/backend/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
