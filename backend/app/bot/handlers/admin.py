from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards import get_admin_keyboard
from app.database import async_session
from app.services.config_service import ConfigService

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    async with async_session() as session:
        is_admin = await ConfigService(session).is_admin(message.from_user.id)
    if not is_admin:
        await message.answer("Нет доступа.")
        return

    await message.answer(
        "🔧 <b>Панель администратора</b>\n\n"
        "Откройте панель управления для просмотра записей, "
        "клиентов и настроек.",
        reply_markup=get_admin_keyboard(),
    )
