# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**GHP IT Hub** — an on-premise, API-first IT management platform (Django REST backend + React frontend). The architecture source of truth is [cloude.md](cloude.md) (Thai); [README.md](README.md) tracks current status and run instructions. Documentation is written in mixed Thai/English — preserve that style when editing docs.

Current state: **module 1 (User Management & Auth)** and **module 2 (Helpdesk & Ticketing)** are implemented. Modules 3–8 from [cloude.md](cloude.md) §2 (Asset, Inventory, Daily Report, Project/Kanban, IPAM, Monitoring) are not yet built. When adding a module, follow the existing `apps/authentication` or `apps/helpdesk` app as the template: subclass `apps.core.BaseModel` for domain models, reuse the auth RBAC permission classes, register the app in `LOCAL_APPS` ([backend/config/settings/base.py](backend/config/settings/base.py)), and mount its `urls` under `/api/v1/<module>/` in [backend/config/urls.py](backend/config/urls.py).

## Commands

All backend commands run inside the `backend` container. The Vite dev server proxies `/api` to `localhost:8000`.

```bash
# Bring up the full dev stack (db + redis + backend + celery + celery-beat)
docker compose up --build

# Run tests — MUST pass the test settings (SQLite in-memory, no Postgres/Redis needed)
docker compose exec backend python manage.py test --settings=config.settings.test
# Single test:
docker compose exec backend python manage.py test apps.authentication.tests.SomeTest.test_method --settings=config.settings.test

# Migrations
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate    # also runs automatically on container start

# Seed one user per role + default departments (admin@ghp.local / Admin@1234, etc.)
docker compose exec backend python manage.py seed_users

# Frontend (run on host, not in Docker)
cd frontend && npm install && npm run dev      # http://localhost:5173
cd frontend && npm run build
cd frontend && npm run lint
```

API docs at `/api/docs/` (Swagger) and `/api/redoc/`; liveness at `/health/`. The backend container entrypoint waits on the DB (`wait_for_db`), migrates, then runs `runserver` — there is no separate migrate step needed for local dev.

## Settings layout

Settings are split: [base.py](backend/config/settings/base.py) holds shared config; `dev.py`, `prod.py`, `test.py` override it. `DJANGO_SETTINGS_MODULE` defaults to `config.settings.dev` (set in `.env` and in [celery.py](backend/config/celery.py)). Always pass `--settings=config.settings.test` for tests — the default dev settings require Postgres + Redis, while test settings use in-memory SQLite, eager Celery, locmem cache, and MD5 password hashing.

Config is read from the environment via `python-decouple` (`config(...)` / `Csv()`), not `os.environ` directly. Copy `.env.example` → `.env` before running.

## Architecture conventions

These patterns are load-bearing — match them when extending the codebase:

- **`apps.core.BaseModel`** ([backend/apps/core/models.py](backend/apps/core/models.py)) — abstract base for all domain models. Gives a UUID primary key, `created_at`/`updated_at`, a `created_by` FK, and an `is_active` soft-delete flag. **`.delete()` is a soft delete** (sets `is_active=False`); use `.hard_delete()` to actually remove a row. The default `objects` manager (`ActiveManager`) hides soft-deleted rows — use `all_objects` to see everything. New domain models should subclass `BaseModel`.
  - Note: the `User`, `Department`, and `AuditLog` models in `authentication` predate this base and define their own UUID/timestamp fields directly rather than inheriting `BaseModel`.

- **Custom user** ([backend/apps/authentication/models.py](backend/apps/authentication/models.py)) — `AUTH_USER_MODEL = "authentication.User"`, keyed by UUID, **logs in by email** (no `username`). Always reference it via `get_user_model()` / `settings.AUTH_USER_MODEL`, never import `User` directly into other apps.

- **RBAC** — three roles on `User.role`: `admin` (Super Admin/IT Manager), `staff` (IT Staff/Engineer), `user` (General User). Use the `user.is_admin` / `user.is_it_staff` properties and the permission classes in [backend/apps/authentication/permissions.py](backend/apps/authentication/permissions.py) (`IsAdmin`, `IsITStaff`, `IsSelfOrAdmin`, `ReadOnlyOrAdmin`) rather than checking roles inline.

- **AuditLog is immutable** — its `save()` raises `ValueError` on any update to an existing row. Only ever create new entries. Login success/failure is audited in `LoginView` ([backend/apps/authentication/views.py](backend/apps/authentication/views.py)); failed logins are caught in an `except` branch because SimpleJWT raises before the view's post-call code runs.

- **JWT auth** — SimpleJWT with rotating + blacklisted refresh tokens. `CustomTokenObtainPairSerializer` injects `email`/`role` claims and returns the full user object in the login response (`{access, refresh, user}`). DRF defaults to `IsAuthenticated` + JWT globally, so new endpoints are auth-required unless overridden.

- **API shape** — versioned under `/api/v1/`, each module mounted as `apps.<module>.urls` from [backend/config/urls.py](backend/config/urls.py). Use DRF `ModelViewSet` + `DefaultRouter`; global defaults provide pagination (`StandardResultsSetPagination`, page size 20), DjangoFilterBackend, search, and ordering — declare `filterset_fields` / `search_fields` / `ordering_fields` on the viewset.

- **LDAP/AD** — off by default. When `LDAP_ENABLED=True`, [base.py](backend/config/settings/base.py) imports [ldap.py](backend/config/settings/ldap.py), which sets `AUTHENTICATION_BACKENDS` to try LDAP first then fall back to local accounts. Keep LDAP-specific config in that module so the `django-auth-ldap`/`python-ldap` dependency stays inert otherwise.

- **Async work** — Celery app is `config` (`celery -A config ...`), Redis broker, `django-celery-beat` DatabaseScheduler for periodic tasks. Put tasks in each app's `tasks.py` (auto-discovered). In tests they run eagerly.

## Frontend

React 18 + Vite + Tailwind + React Router. Auth state lives in [frontend/src/lib/auth.jsx](frontend/src/lib/auth.jsx) (`AuthProvider` / `useAuth`); the API client [frontend/src/lib/api.js](frontend/src/lib/api.js) stores JWTs in `localStorage` and transparently refreshes on a 401 (single in-flight refresh, replays the original request, redirects to `/login` on failure). Route new API calls through the shared `api` axios instance so the token-refresh interceptor applies.
