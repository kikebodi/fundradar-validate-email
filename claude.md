# Agent Guidelines for fundradar-validate-email

This document defines **strict rules** for AI coding agents working on this codebase.
All rules are mandatory.

---

## Core Principles

All code MUST be production-ready.

"Production-ready" means:

- Async-first execution
- Optimal time and space complexity
- No unnecessary abstractions or dead code
- Minimal latency for API responses
- Clear separation of concerns across layers

If the code is not fully optimized, fix it before returning.

---

## Project Purpose

Async FastAPI service that sends a validation email through Resend when a
new row is inserted into the Supabase `companies` table.

---

## Architecture — Presentation / Business / Domain

The codebase follows a strict layered structure (same convention as
`fundradar-company-research`):

```
/presentation              Thin HTTP layer — no business logic
  /webhooks
    company_created.py     Supabase webhook router
    schemas.py             Transport DTOs (CompanyCreatedWebhook, WebhookAck)
  /api
    health.py              GET /health
  dependencies.py          FastAPI Depends helpers (typed)

/business                  Use cases and adapters
  /config
    settings.py            .env + shell env loader, .env wins
  /interfaces              Ports (ABCs)
    email_sender.py        EmailSender + EmailSendError
    template_renderer.py   TemplateRenderer
  /services                Concrete adapters
    resend_email_sender.py       Resend HTTP adapter (httpx)
    jinja_template_renderer.py   Jinja2 adapter (StrictUndefined, autoescape)
    validation_email_service.py  Orchestrator
  factory.py               Wires production adapters from settings

/domain                    Pure entities and value objects
  /models
    company.py             Company
    email.py               EmailMessage, ValidationLinks, SendResult

/templates                 HTML email templates (validate_email_template.html)
/tests                     pytest + asyncio
main.py                    FastAPI entrypoint at repo root
```

### Layer rules (NON-NEGOTIABLE)

- **Domain** depends on nothing except `pydantic`. No I/O, no framework
  imports, no business logic.
- **Business** depends on `domain` and the standard library / approved
  libraries. It MUST NOT import from `presentation`.
- **Business** orchestrators (`*_service.py`) depend only on **interfaces**
  (ports), never on concrete adapters.
- **Presentation** depends on `business` and `domain`. It MUST NOT contain
  business logic, template rendering, or external API calls.
- New external integrations go behind a port in `business/interfaces/` with
  a concrete adapter in `business/services/`.

### Wiring

- `business/factory.py` constructs concrete adapters from settings.
- `main.py` calls the factory inside the FastAPI lifespan, attaches the
  orchestrator to `app.state.validation_email_service`, and closes the
  sender on shutdown.
- Routes pull dependencies via `presentation/dependencies.py`
  (`ValidationEmailServiceDep`).
- Tests bypass the factory and inject doubles directly into `app.state`.

---

## System Constraints

- Backend framework: **FastAPI**
- ASGI server: **Hypercorn**
- Email provider: **Resend** (HTTP API via `httpx.AsyncClient`)
- Template engine: **Jinja2** (autoescape on, `StrictUndefined`)
- Deployment: **Railway via Dockerfile**
- Config source: `.env` (local) + Railway environment variables

---

## Environment & Configuration

- Settings live in `business/config/settings.py` as a `pydantic.BaseModel`.
- Loader merges shell env (lowest priority) with `.env` values (highest);
  every value is `.strip()`ed to defend against trailing newlines in pasted
  secrets.
- `get_settings()` is `lru_cache`d.
- `.env` MUST be in `.gitignore` (already enforced).
- Secrets MUST NEVER be hardcoded.
- `RESEND_API_KEY` and `FROM_EMAIL` are required; the factory raises
  `RuntimeError` at use time if either is missing, so the server can still
  boot for healthchecks without them.

### Required keys

| Key | Required | Notes |
| --- | --- | --- |
| `RESEND_API_KEY` | yes | Resend Bearer token |
| `FROM_EMAIL` | yes | Verified sender, e.g. `FundRadar <noreply@fundradar.ai>` |
| `BASE_URL` | no | Defaults to `https://fundradar.ai` |
| `REQUEST_TIMEOUT` | no | Float seconds, default `10.0` |
| `MAX_RETRIES` | no | Int, default `3` |
| `LOG_LEVEL` | no | Default `INFO` |
| `WEBHOOK_SECRET` | no | Optional Supabase shared secret |

---

## Async & Performance Rules

- ALL I/O MUST BE ASYNC. No blocking calls in request paths.
- The Resend adapter owns a single pooled `httpx.AsyncClient` for the
  process lifetime; do not instantiate per-request clients.
- Retries: exponential backoff on `429` and `5xx`, plus `httpx.TransportError`,
  capped by `MAX_RETRIES`.

---

## Preferred Libraries (MANDATORY)

Web/API:
- `fastapi`
- `hypercorn`

HTTP:
- `httpx` (async, pooled)

Templating:
- `jinja2`

Validation:
- `pydantic` v2
- `email-validator` (transitive — needed for `EmailStr`)
- `python-dotenv`

Testing:
- `pytest`
- `pytest-asyncio`
- `asgi-lifespan`
- `httpx` (ASGITransport)

Add a new dependency only by pinning it in `requirements.txt`.

---

## External API Clients

- All external services MUST live in `business/services/` behind a port in
  `business/interfaces/`.
- Resend uses `httpx.AsyncClient` with timeout, connection pool, and retry.
- API keys are passed in via the constructor — never imported from settings
  inside the adapter.

---

## FastAPI Rules

- Use `APIRouter` per concern, included from `main.create_app()`.
- Validate all inbound payloads with Pydantic models in
  `presentation/webhooks/schemas.py`.
- Routes return typed Pydantic responses.
- Routes translate `EmailSendError` → `HTTPException(502)`. They do NOT
  raise other exception types directly.
- `/` and `/health` are reserved for readiness probes.

---

## Templating Rules

- Templates live in `/templates`.
- `JinjaTemplateRenderer` uses `select_autoescape` for `html`/`xml` and
  `StrictUndefined` so missing variables raise.
- The orchestrator passes a flat dict context: `client_id`, `client_name`,
  `validate_url`, `unsubscribe_url`. Adding a new variable to the template
  MUST also add it to `ValidationEmailService._render`.

---

## Code Style

- PEP 8, max line length 88.
- `from __future__ import annotations` at the top of every Python file.
- snake_case / PascalCase / UPPER_CASE.
- Prefer early returns. No mutable default arguments.

---

## Type Safety

- Full type annotations required on every signature.
- No `Any`. Use `Protocol`, `ABC`, or concrete types.
- Pydantic v2 models for all data crossing layer boundaries.

---

## Error Handling

- No bare `except`.
- Business adapters raise typed errors defined in
  `business/interfaces/` (e.g. `EmailSendError`).
- Presentation translates these into HTTP errors. No silent failures.

---

## Logging

- Module-scope `logger = logging.getLogger(__name__)`.
- No `print()`.
- Log levels configured via `LOG_LEVEL` setting.
- NEVER log `RESEND_API_KEY`, recipient PII beyond email/UUID, or full
  HTML bodies.

---

## Function Design

- Single responsibility.
- Max 5 parameters.
- Constructor injection for collaborators.
- No globals other than `get_settings()` (cached).

---

## Testing

- `pytest` + `pytest-asyncio` (auto mode via `pytest.ini`).
- All endpoint tests run through `LifespanManager` + `httpx.ASGITransport`.
- External I/O MUST be mocked. Tests inject stub services into
  `app.state.validation_email_service` instead of patching modules.
- Domain renders are tested by exercising `ValidationEmailService` with a
  stub `EmailSender` (no network).

---

## Security

- Secrets in `.env` only.
- Validate all inbound webhook payloads with Pydantic.
- `WEBHOOK_SECRET` (when set) MUST be checked before doing any work — the
  current handler does not yet enforce this; add header verification in
  the route if/when this becomes required.

---

## Dependencies

- Define dependencies in `requirements.txt`. Pin versions explicitly.
- Local development uses `python -m venv .venv` + `pip install -r requirements.txt`.
- Do NOT introduce `pyproject.toml`, `Pipfile`, or `environment.yml`.

---

## Railway Deployment

- Deployed as a Docker image. `railway.json` points at `Dockerfile` with
  `"builder": "DOCKERFILE"`.
- Healthcheck path: `/`.
- Container runs:
  ```
  hypercorn main:app --bind "0.0.0.0:${PORT:-8080}"
  ```
- `Dockerfile` is the single source of truth for the start command (no
  `Procfile`).
- Stateless only. No local persistence.

---

## Before Commit

- Tests pass: `pytest`
- App boots: `python -c "from main import create_app; create_app()"`
- No secrets in diff
- Async verified — no `requests`, no `time.sleep`, no blocking calls
- Adapters isolated in `business/services/`
- New external calls go through a port in `business/interfaces/`

---

## Non-Negotiable

- No sync I/O in request paths
- No business logic in `presentation/`
- No external API calls outside `business/services/`
- No untyped responses
- No silent failures
- No imports from `presentation` inside `business` or `domain`
- No imports from `business` inside `domain`

---

## Priority

1. Correctness
2. Performance
3. Security
4. Maintainability
