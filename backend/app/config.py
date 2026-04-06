from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str = ""
    ADMIN_TELEGRAM_ID: int = 0
    WEBAPP_URL: str = "https://vadimkolobanov-daina-be95.twc1.net"
    BOT_USERNAME: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/daina"

    # App
    APP_NAME: str = "DAINA Nail Studio"
    MASTER_NAME: str = "Мастер"
    STUDIO_ADDRESS: str = ""
    STUDIO_MAP_URL: str = ""

    # Admin access — comma-separated telegram IDs (in addition to ADMIN_TELEGRAM_ID)
    ADMIN_IDS: str = ""

    # Notifications
    REMINDER_24H: bool = True
    REMINDER_2H: bool = True
    FOLLOWUP_ENABLED: bool = True
    CORRECTION_DAYS: int = 21

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def get_admin_ids(self) -> set[int]:
        """Get all admin telegram IDs (from ADMIN_TELEGRAM_ID + ADMIN_IDS)."""
        ids = set()
        if self.ADMIN_TELEGRAM_ID:
            ids.add(self.ADMIN_TELEGRAM_ID)
        if self.ADMIN_IDS:
            for raw in self.ADMIN_IDS.split(","):
                raw = raw.strip()
                if raw.isdigit():
                    ids.add(int(raw))
        return ids


settings = Settings()
