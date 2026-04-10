from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import settings


def get_main_keyboard() -> InlineKeyboardMarkup:
    url = settings.WEBAPP_URL
    if url.startswith("https://"):
        btn = InlineKeyboardButton(
            text="💅 Открыть личный кабинет",
            web_app=WebAppInfo(url=url),
        )
    else:
        btn = InlineKeyboardButton(
            text="💅 Открыть личный кабинет",
            url=url,
        )
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])


def get_admin_keyboard() -> InlineKeyboardMarkup:
    url = settings.WEBAPP_URL
    if url.startswith("https://"):
        btn = InlineKeyboardButton(
            text="📊 Панель управления",
            web_app=WebAppInfo(url=f"{url}?startapp=admin"),
        )
    else:
        btn = InlineKeyboardButton(
            text="📊 Панель управления",
            url=f"{url}?startapp=admin",
        )
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])
