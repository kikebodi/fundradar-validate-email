# fundradar-validate-email

Async FastAPI service that sends a validation email through Resend when a new
row is inserted into the Supabase `companies` table.

## Architecture

```
/app
  /api        FastAPI routers (no business logic)
  /services   email orchestration
  /clients    Resend HTTP client (async httpx)
  /models     Pydantic v2 schemas
  /core       config, logging, template env
/templates    HTML email templates
/tests        pytest + asyncio
```

Trigger flow:

```
Supabase webhook -> POST /webhooks/supabase/company-created
                 -> EmailService.send_validation_email
                 -> ResendClient -> Resend API
```

## Local setup

```bash
conda env create -f environment.yml
conda activate fundradar-validate-email
cp .env.example .env  # fill in RESEND_API_KEY + FROM_EMAIL
uvicorn app.main:app --reload
```

The service exposes:

- `GET /health`
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

## Configuration (.env)

| Var | Required | Default |
| --- | --- | --- |
| `RESEND_API_KEY` | yes | — |
| `FROM_EMAIL` | yes | — |
| `BASE_URL` | no | `https://fundradar.ai` |
| `REQUEST_TIMEOUT` | no | `10.0` |
| `MAX_RETRIES` | no | `3` |
| `PORT` | no | `8000` |

## Railway deployment

Start command:

```
hypercorn app.main:app --bind 0.0.0.0:$PORT
```

Configured in `Procfile` and `railway.toml`. Health check path: `/health`.

## Tests

```bash
pytest
```
