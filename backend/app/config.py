from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Infrastructure (not configurable via UI)
    BOT_TOKEN: str = ""
    ADMIN_TELEGRAM_ID: int = 0
    WEBAPP_URL: str = "https://vadimkolobanov-daina-be95.twc1.net"
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/daina"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
