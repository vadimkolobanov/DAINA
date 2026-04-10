from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.app_config import AppConfig

# Keys that can be managed via admin panel
CONFIGURABLE_KEYS = {
    # Studio
    "app_name",
    "studio_address",
    "studio_map_url",
    "currency",
    # Master
    "master_name",
    "master_username",
    "master_phone",
    "master_instagram",
    # Bot
    "bot_username",
    "admin_ids",
    # Schedule
    "slot_interval",
    "correction_days",
    # Notifications
    "reminder_24h",
    "reminder_2h",
    "followup_enabled",
    # Texts
    "care_tips",
    "vip_message",
}

# Default values (used until admin configures via UI)
_DEFAULTS = {
    "admin_ids": lambda: str(settings.ADMIN_TELEGRAM_ID) if settings.ADMIN_TELEGRAM_ID else "",
    "bot_username": "",
    "app_name": "DAINA Nail Studio",
    "master_name": "Мастер",
    "master_username": "",
    "master_phone": "",
    "master_instagram": "",
    "studio_address": "",
    "studio_map_url": "",
    "correction_days": "21",
    "reminder_24h": "true",
    "reminder_2h": "true",
    "followup_enabled": "true",
    "slot_interval": "30",
    "currency": "руб",
    "care_tips": (
        "Первые 2-3 часа избегайте контакта с водой\n"
        "Не используйте ацетонсодержащие средства\n"
        "Наносите масло для кутикулы ежедневно\n"
        "Используйте перчатки при уборке и мытье посуды"
    ),
    "vip_message": (
        "Вам присвоен VIP-статус! 💎\n"
        "Теперь вы в числе особенных клиентов.\n"
        "Спасибо за доверие!"
    ),
}


def _default(key: str) -> str:
    """Resolve default value (callable or plain string)."""
    val = _DEFAULTS.get(key, "")
    return val() if callable(val) else val


class ConfigService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> str:
        """Get config value by key. Falls back to default."""
        result = await self.session.execute(
            select(AppConfig).where(AppConfig.key == key)
        )
        config = result.scalar_one_or_none()
        if config is not None:
            return config.value
        return _default(key)

    async def get_all(self) -> dict[str, str]:
        """Get all config values."""
        result = await self.session.execute(select(AppConfig))
        db_configs = {c.key: c.value for c in result.scalars().all()}
        merged = {}
        for key in CONFIGURABLE_KEYS:
            if key in db_configs:
                merged[key] = db_configs[key]
            else:
                merged[key] = _default(key)
        return merged

    async def set(self, key: str, value: str) -> None:
        """Set a config value."""
        if key not in CONFIGURABLE_KEYS:
            raise ValueError(f"Unknown config key: {key}")
        result = await self.session.execute(
            select(AppConfig).where(AppConfig.key == key)
        )
        config = result.scalar_one_or_none()
        if config:
            config.value = value
        else:
            self.session.add(AppConfig(key=key, value=value))
        await self.session.commit()

    async def set_many(self, data: dict[str, str]) -> None:
        """Set multiple config values at once."""
        for key, value in data.items():
            if key not in CONFIGURABLE_KEYS:
                continue
            result = await self.session.execute(
                select(AppConfig).where(AppConfig.key == key)
            )
            config = result.scalar_one_or_none()
            if config:
                config.value = value
            else:
                self.session.add(AppConfig(key=key, value=value))
        await self.session.commit()

    async def get_admin_ids(self) -> set[int]:
        """Get all admin IDs from DB + bootstrap env admin."""
        ids: set[int] = set()
        # Bootstrap admin from .env (always included)
        if settings.ADMIN_TELEGRAM_ID:
            ids.add(settings.ADMIN_TELEGRAM_ID)
        # Additional admins from database (managed via UI)
        db_ids_str = await self.get("admin_ids")
        if db_ids_str:
            for raw in db_ids_str.split(","):
                raw = raw.strip()
                if raw.isdigit():
                    ids.add(int(raw))
        return ids

    async def is_admin(self, telegram_id: int) -> bool:
        """Check if a telegram user ID is an admin."""
        admin_ids = await self.get_admin_ids()
        return telegram_id in admin_ids
