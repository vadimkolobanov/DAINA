from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import settings


def get_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💅 Записаться на маникюр",
                    web_app=WebAppInfo(url=settings.WEBAPP_URL),
                )
            ],
            [
                InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings"),
                InlineKeyboardButton(text="🖼 Наши работы", callback_data="gallery"),
            ],
        ]
    )


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Панель управления",
                    web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}?mode=admin"),
                )
            ],
        ]
    )
