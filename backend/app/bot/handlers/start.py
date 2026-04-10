from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards import get_main_keyboard
from app.database import async_session
from app.services.client_service import ClientService
from app.services.config_service import ConfigService

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        svc = ClientService(session)
        config_svc = ConfigService(session)

        # Check for deeplink referral (e.g., /start ref_abc123)
        args = message.text.split(maxsplit=1)
        referral_code = None
        if len(args) > 1 and args[1].startswith("ref_"):
            referral_code = args[1][4:]  # remove "ref_" prefix

        # If deeplink points to a pre-created Instagram client, link them first
        is_new = False
        if referral_code:
            existing = await svc.get_by_referral_code(referral_code)
            if existing and existing.telegram_id is None:
                existing.telegram_id = message.from_user.id
                existing.first_name = message.from_user.first_name
                existing.last_name = message.from_user.last_name
                existing.username = message.from_user.username
                await session.commit()
                client = existing
                is_new = True
            else:
                client, is_new = await svc.get_or_create(
                    telegram_id=message.from_user.id,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    username=message.from_user.username,
                )
        else:
            client, is_new = await svc.get_or_create(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
            )

        app_name = await config_svc.get("app_name")
        master_name = await config_svc.get("master_name")

    if is_new:
        text = (
            f"Добро пожаловать в <b>{app_name}</b>! ✨\n\n"
            f"Я — {master_name}, и я рада видеть вас здесь.\n\n"
            f"Здесь вы можете удобно записаться на маникюр, "
            f"просмотреть мои работы и управлять своими записями.\n\n"
            f"Нажмите кнопку ниже, чтобы начать 👇"
        )
    else:
        text = (
            f"С возвращением, <b>{client.first_name}</b>! 💅\n\n"
            f"Рада вас снова видеть. Хотите записаться?"
        )

    await message.answer(text, reply_markup=get_main_keyboard())
