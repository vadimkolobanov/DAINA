from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str = ""
    ADMIN_TELEGRAM_ID: int = 0
    WEBAPP_URL: str = "https://vadimkolobanov-daina-be95.twc1.net"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/daina"

    # App
    APP_NAME: str = "DAINA Nail Studio"
    MASTER_NAME: str = "Мастер"
    STUDIO_ADDRESS: str = ""
    STUDIO_MAP_URL: str = ""

    # Notifications
    REMINDER_24H: bool = True
    REMINDER_2H: bool = True
    FOLLOWUP_ENABLED: bool = True
    CORRECTION_DAYS: int = 21

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
