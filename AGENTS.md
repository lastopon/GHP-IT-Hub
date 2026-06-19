# AGENTS.md

## Project context
- This is **GHP IT Hub** — an on-premise, API-first IT management platform.
- The architecture source of truth is [cloude.md](cloude.md); see [README.md](README.md) for current status and how to run.
- Implementation has started: **Skeleton + Phase 1 (module 1 — User Management & Auth)** is complete.
  - Backend: Python 3.12 / Django 5 / DRF / SimpleJWT / Celery in [backend/](backend/) (apps `core`, `authentication`).
  - Frontend: React + Vite + Tailwind in [frontend/](frontend/).
  - Dev stack: [docker-compose.yml](docker-compose.yml) (Django + PostgreSQL + Redis + Celery + beat).
- Modules 2–8 are not yet implemented (placeholders only on the dashboard).

## How to work here
- Prefer documentation updates and clarifications unless the user explicitly asks for code changes.
- When proposing changes, align them with the architecture and module structure described in [cloude.md](cloude.md).
- Keep wording concise, structured, and consistent with the existing Thai documentation style.
- If a task requires implementation, first confirm the intended stack, folder layout, and conventions before making assumptions.

## Expectations for agents
- Do not invent missing files, commands, or runtime behavior.
- Link to [cloude.md](cloude.md) for project context instead of repeating its content.
- If new documentation is added, make it easy to scan and easy to trace back to the relevant section in the architecture document.
