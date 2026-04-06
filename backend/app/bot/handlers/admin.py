from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import get_admin_keyboard
from app.config import settings

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in settings.get_admin_ids():
        await message.answer("Нет доступа.")
        return

    await message.answer(
        "🔧 <b>Панель администратора</b>\n\n"
        "Откройте панель управления для просмотра записей, "
        "клиентов и настроек.",
        reply_markup=get_admin_keyboard(),
    )
