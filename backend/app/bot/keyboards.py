from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import settings


def get_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💅 Открыть личный кабинет",
                    web_app=WebAppInfo(url=settings.WEBAPP_URL),
                )
            ],
        ]
    )


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Панель управления",
                    web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}?startapp=admin"),
                )
            ],
        ]
    )
