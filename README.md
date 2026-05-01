# fundradar-validate-email

Async FastAPI service that sends a validation email through Resend when a new
row is inserted into the Supabase `companies` table.

## Architecture

The codebase follows a Presentation / Business / Domain layered structure
(same convention as [`fundradar-company-research`](https://github.com/kikebodi/fundradar-company-research)):

```
/presentation              Thin HTTP layer — no business logic
  /webhooks
    company_created.py     Supabase webhook router
    schemas.py             Transport DTOs
  /api
    health.py
  dependencies.py          FastAPI DI helpers

/business                  Use cases and adapters
  /config
    settings.py            .env + shell env loader
  /interfaces              Ports (ABCs)
    email_sender.py        EmailSender
    template_renderer.py   TemplateRenderer
  /services                Concrete adapters
    resend_email_sender.py
    jinja_template_renderer.py
    validation_email_service.py    Orchestrator
  factory.py               Wires production adapters from settings

/domain                    Pure entities and value objects
  /models
    company.py             Company
    email.py               EmailMessage, ValidationLinks, SendResult

/templates                 HTML email templates
/tests                     pytest + asyncio
main.py                    FastAPI entrypoint
```

Flow:

```
Supabase webhook
  -> presentation/webhooks/company_created.py
  -> business/services/validation_email_service.py
  -> business/services/jinja_template_renderer.py  (renders HTML)
  -> business/services/resend_email_sender.py      (POST api.resend.com)
```

The orchestrator depends only on the `EmailSender` and `TemplateRenderer`
ports — swap either adapter without touching domain or presentation.

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in RESEND_API_KEY + FROM_EMAIL
hypercorn main:app --bind 0.0.0.0:8000 --reload
```

The service exposes:

- `GET /` — readiness probe (used by Railway healthcheck)
- `GET /health` — same shape as `/`, kept for backwards compat
- `POST /webhooks/supabase/company-created`

### Example webhook payload

```json
{
  "type": "INSERT",
  "table": "companies",
  "schema": "public",
  "record": {
    "id": "9b1c4f9a-1e90-4d2b-a4e6-3a4d3f0d9c11",
    "email": "founder@example.com",
    "name": "Acme Inc"
  }
}
```

The handler returns `202 Accepted` with the Resend message id.

### Call the endpoint locally with fake data

With the server running on `http://127.0.0.1:8000`:

```bash
curl -i -X POST http://127.0.0.1:8000/webhooks/supabase/company-created \
  -H "Content-Type: application/json" \
  -d '{
    "type": "INSERT",
    "table": "companies",
    "schema": "public",
    "record": {
      "id": "9b1c4f9a-1e90-4d2b-a4e6-3a4d3f0d9c11",
      "email": "founder@example.com",
      "name": "Acme Inc"
    }
  }'
```

Expected response:

```
HTTP/1.1 202 Accepted
content-type: application/json

{"status":"accepted","message_id":"<resend-message-id>"}
```

Health check:

```bash
curl -s http://127.0.0.1:8000/health
# {"status":"ok"}
```

> Tip: set `FROM_EMAIL` to a sender verified in your Resend dashboard, and use a
> recipient you control (e.g. your own address) so the test email actually
> lands. With an invalid `RESEND_API_KEY` you'll get a `502 Bad Gateway`.

## Configuration (.env)

| Var | Required | Default |
| --- | --- | --- |
| `RESEND_API_KEY` | yes | — |
| `FROM_EMAIL` | yes | — |
| `BASE_URL` | no | `https://fundradar.ai` |
| `REQUEST_TIMEOUT` | no | `10.0` |
| `MAX_RETRIES` | no | `3` |

## Railway deployment

Deployed as a Docker image. `railway.json` points Railway at `Dockerfile`,
which runs:

```
hypercorn main:app --bind 0.0.0.0:8000
```

Healthcheck path: `/`. Build context filtered by `.dockerignore`.

## Tests

```bash
pytest
```
