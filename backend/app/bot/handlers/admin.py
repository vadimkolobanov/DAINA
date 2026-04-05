from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import get_admin_keyboard
from app.config import settings

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != settings.ADMIN_TELEGRAM_ID:
        await message.answer("Нет доступа.")
        return

    await message.answer(
        "🔧 <b>Панель администратора</b>\n\n"
        "Откройте панель управления для просмотра записей, "
        "клиентов и настроек.",
        reply_markup=get_admin_keyboard(),
    )
