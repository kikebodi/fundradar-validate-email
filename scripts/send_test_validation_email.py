"""Manual end-to-end test for the EmailService.

Sends a real validation email through Resend using the configured .env.
Not part of the automated suite — run it by hand when you want to verify
that template rendering, the Resend client, and your sender domain all
work together.

Usage:

    python scripts/send_test_validation_email.py --to founder@example.com
    python scripts/send_test_validation_email.py \
        --to founder@example.com \
        --name "Acme Inc" \
        --client-id 9b1c4f9a-1e90-4d2b-a4e6-3a4d3f0d9c11

Requires RESEND_API_KEY and FROM_EMAIL in your .env (or environment).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID, uuid4

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.clients.resend_client import ResendClient, ResendError  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.core.templates import build_template_env  # noqa: E402
from app.services.email_service import EmailService  # noqa: E402

logger = get_logger("scripts.send_test_validation_email")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a real FundRadar validation email via Resend.",
    )
    parser.add_argument(
        "--to",
        required=True,
        help="Recipient email address (use one you control).",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Optional client_name to inject into the template.",
    )
    parser.add_argument(
        "--client-id",
        default=None,
        help="Optional UUID. Generated if omitted.",
    )
    return parser.parse_args()


def resolve_client_id(raw: str | None) -> UUID:
    if raw is None:
        return uuid4()
    try:
        return UUID(raw)
    except ValueError as exc:
        raise SystemExit(f"--client-id must be a valid UUID: {raw}") from exc


async def run(recipient: str, client_id: UUID, client_name: str | None) -> int:
    configure_logging()
    settings = get_settings()

    client = ResendClient(
        api_key=settings.resend_api_key,
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
    )
    service = EmailService(
        client=client,
        env=build_template_env(),
        from_email=settings.from_email,
        base_url=settings.base_url,
    )

    logger.info(
        "sending validation email recipient=%s client_id=%s name=%s base_url=%s",
        recipient,
        client_id,
        client_name,
        settings.base_url,
    )
    try:
        response = await service.send_validation_email(
            recipient=recipient,
            client_id=client_id,
            client_name=client_name,
        )
    except ResendError as exc:
        logger.error("resend_error status=%s message=%s", exc.status_code, exc)
        return 1
    finally:
        await client.aclose()

    print(f"OK message_id={response.id}")
    print(f"   client_id={client_id}")
    print(f"   validate={settings.base_url.rstrip('/')}/validate?id={client_id}")
    print(f"   unsubscribe={settings.base_url.rstrip('/')}/unsubscribe?id={client_id}")
    return 0


def main() -> int:
    args = parse_args()
    client_id = resolve_client_id(args.client_id)
    return asyncio.run(run(args.to, client_id, args.name))


if __name__ == "__main__":
    raise SystemExit(main())
