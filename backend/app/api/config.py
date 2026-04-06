from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_current_telegram_user, require_admin
from app.services.config_service import ConfigService

router = APIRouter(prefix="/api/config", tags=["config"])


class ConfigUpdate(BaseModel):
    """Update config values. Only known keys are accepted."""
    values: dict[str, str]


@router.get("/check-admin")
async def check_admin(
    telegram_id: int | None = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    """Check if the current user is an admin."""
    if not telegram_id:
        return {"is_admin": False}
    config_svc = ConfigService(session)
    is_admin = await config_svc.is_admin(telegram_id)
    return {"is_admin": is_admin, "telegram_id": telegram_id}


@router.get("/public")
async def get_public_config(session: AsyncSession = Depends(get_session)):
    """Get public config values (no admin required)."""
    config_svc = ConfigService(session)
    all_config = await config_svc.get_all()
    # Only expose safe public values
    return {
        "app_name": all_config.get("app_name", ""),
        "bot_username": all_config.get("bot_username", ""),
        "studio_address": all_config.get("studio_address", ""),
        "studio_map_url": all_config.get("studio_map_url", ""),
        "master_username": all_config.get("master_username", ""),
        "currency": all_config.get("currency", "руб"),
    }


@router.get("")
async def get_config(
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Get all config values (admin only)."""
    config_svc = ConfigService(session)
    return await config_svc.get_all()


@router.put("")
async def update_config(
    data: ConfigUpdate,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Update config values (admin only)."""
    config_svc = ConfigService(session)
    await config_svc.set_many(data.values)
    return {"ok": True}
