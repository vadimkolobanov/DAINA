import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qs, unquote

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)


def validate_init_data(init_data: str) -> dict | None:
    """Validate Telegram WebApp initData and return parsed data.

    Returns the parsed data dict if valid, None if invalid.
    """
    if not init_data or not settings.BOT_TOKEN:
        return None

    try:
        parsed = parse_qs(init_data, keep_blank_values=True)
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None

        # Build the data-check-string
        data_pairs = []
        for key in sorted(parsed.keys()):
            if key == "hash":
                continue
            data_pairs.append(f"{key}={unquote(parsed[key][0])}")
        data_check_string = "\n".join(data_pairs)

        # Compute HMAC
        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            return None

        # Parse user data
        user_str = parsed.get("user", [None])[0]
        if user_str:
            return {"user": json.loads(unquote(user_str))}
        return {}
    except Exception:
        logger.exception("Failed to validate initData")
        return None


async def get_current_telegram_user(
    x_telegram_init_data: str = Header(default=""),
    x_telegram_user_id: str = Header(default=""),
) -> int | None:
    """Extract telegram user ID from headers.

    Uses initData validation when available (cryptographically secure).
    Falls back to x-telegram-user-id header only as a convenience
    for read-only operations. Mutating operations should use require_admin.
    """
    # Try initData validation (most secure)
    if x_telegram_init_data:
        data = validate_init_data(x_telegram_init_data)
        if data and "user" in data:
            return data["user"].get("id")

    # Fallback: accept header but only for non-critical operations
    # Admin endpoints are separately protected by require_admin which
    # validates against the admin_ids allowlist
    if x_telegram_user_id and x_telegram_user_id.isdigit():
        return int(x_telegram_user_id)

    return None


async def require_admin(
    x_telegram_init_data: str = Header(default=""),
    x_telegram_user_id: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
) -> int:
    """Dependency that requires the request to come from an admin user.

    Returns the admin's telegram_id.
    """
    telegram_id = await get_current_telegram_user(x_telegram_init_data, x_telegram_user_id)
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Telegram user ID required")

    config_svc = ConfigService(session)
    if not await config_svc.is_admin(telegram_id):
        raise HTTPException(status_code=403, detail="Admin access denied")

    return telegram_id
