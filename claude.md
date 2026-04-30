# Agent Guidelines for Python Code Quality (FastAPI + AI Agents)

This document defines **strict rules** for AI coding agents working on this codebase.  
All rules are mandatory.

---

## Core Principles

All code MUST be production-ready.

“Production-ready” means:

- Optimal time and space complexity
- Designed for async-first execution
- No unnecessary abstractions or dead code
- Minimal latency for API responses
- Clear separation of concerns (API / services / infra)

If the code is not fully optimized, fix it before returning.

---

## System Architecture Constraints

- Backend framework: FastAPI
- ASGI server: Hypercorn
- Deployment: Railway
- Email provider: Resend API
- Config source: .env (local) + Railway environment variables

Structure MUST follow:

/app
  /api
  /services
  /clients
  /models
  /core
/tests

---

## Environment & Configuration

- MUST load config using pydantic.BaseSettings
- MUST support .env locally via python-dotenv
- MUST NOT hardcode secrets

Example:

class Settings(BaseSettings):
    resend_api_key: str
    openai_api_key: str

    class Config:
        env_file = ".env"

- .env MUST be in .gitignore
- Railway variables MUST mirror .env keys

---

## Async & Performance Rules

- ALL I/O MUST BE ASYNC
- NEVER block the event loop
- Use connection pooling
- Use batching for LLM or scraping calls

---

## Preferred Libraries (MANDATORY)

Web/API:
- fastapi
- hypercorn

Scraping:
- crawl4ai

LLM:
- openai
- instructor

Validation:
- pydantic v2
- python-dotenv

Testing:
- pytest
- pytest-asyncio
- httpx

---

## External API Clients

All external services MUST be in /clients.

Resend:
- Use httpx.AsyncClient
- Implement timeout + retries
- Never expose API key

---

## FastAPI Rules

- Use APIRouter
- Use dependency injection
- Validate with Pydantic
- Return typed responses

---

## LLM Rules

- Use instructor
- Structured outputs only
- Define strict schemas
- Minimize token usage

---

## Scraping Rules

- Use crawl4ai
- Async only
- Implement timeout, retry, limits

---

## Code Style

- PEP 8
- Max 88 chars
- Ruff enforced
- snake_case / PascalCase / UPPER_CASE

---

## Type Safety

- Full typing required
- No Any
- Must pass mypy

---

## Error Handling

- No bare except
- Structured logging only

---

## Logging

- Central logger
- No print()
- No secrets in logs

---

## Function Design

- Single responsibility
- Max 5 params
- Early returns
- No mutable defaults

---

## Testing

- pytest required
- Async tests for endpoints
- Mock all externals

---

## Security

- Secrets in .env only
- Validate inputs
- Sanitize scraped data

---

## Dependencies

- Use conda for environment and dependency management
- Define environments using environment.yml (NOT pyproject.toml)
- Pin versions explicitly for reproducibility

---

## Railway Deployment

PORT = os.getenv("PORT", 8000)

Start:
hypercorn app.main:app --bind 0.0.0.0:$PORT

- Stateless only
- No local persistence

---

## Before Commit

- Tests pass
- mypy passes
- ruff passes
- No secrets
- Async verified
- Clients isolated

---

## Non-Negotiable

- No sync I/O
- No business logic in routes
- No direct external calls
- No untyped responses
- No silent failures

---

## Priority

1. Correctness
2. Performance
3. Security
4. Maintainability