from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.bot.bot import bot
from app.config import settings
from app.database import async_session
from app.models.booking import BookingStatus
from app.services.booking_service import BookingService
from app.services.client_service import ClientService
from app.services.config_service import ConfigService
from app.services.notification_service import NotificationService

router = Router()


@router.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery):
    """Show client's bookings."""
    async with async_session() as session:
        client_svc = ClientService(session)
        client = await client_svc.get_by_telegram_id(callback.from_user.id)
        if not client:
            await callback.answer("У вас пока нет записей", show_alert=True)
            return

        booking_svc = BookingService(session)
        bookings = await booking_svc.get_client_bookings(client.id)

    if not bookings:
        await callback.answer("У вас пока нет записей", show_alert=True)
        return

    status_emoji = {
        "pending": "🕐",
        "confirmed": "✅",
        "completed": "✅",
        "cancelled": "❌",
        "no_show": "⚠️",
    }
    status_label = {
        "pending": "Ожидает",
        "confirmed": "Подтверждено",
        "completed": "Завершено",
        "cancelled": "Отменено",
        "no_show": "Не пришёл",
    }

    text = "📋 <b>Ваши записи:</b>\n\n"
    for b in bookings[:10]:
        s = b.status.value
        text += (
            f"{status_emoji.get(s, '❓')} <b>{b.service.name}</b>\n"
            f"   {b.date.strftime('%d.%m.%Y')} • {b.time_start.strftime('%H:%M')}–{b.time_end.strftime('%H:%M')}\n"
            f"   Статус: {status_label.get(s, s)}\n\n"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💅 Записаться", web_app=WebAppInfo(url=settings.WEBAPP_URL))],
        ]
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "gallery")
async def gallery(callback: CallbackQuery):
    """Placeholder for gallery."""
    await callback.answer("Галерея работ скоро будет доступна!", show_alert=True)


@router.callback_query(F.data.startswith("confirm_"))
async def confirm_booking(callback: CallbackQuery):
    """Admin confirms a booking."""
    if callback.from_user.id not in settings.get_admin_ids():
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        booking_id = int(callback.data.removeprefix("confirm_"))
    except ValueError:
        await callback.answer("Ошибка данных", show_alert=True)
        return
    async with async_session() as session:
        svc = BookingService(session)
        booking = await svc.update_status(booking_id, BookingStatus.CONFIRMED)
        if booking:
            config = await ConfigService(session).get_all()
            notifier = NotificationService(bot, config)
            await notifier.notify_client_confirmed(booking)
            await callback.message.edit_text(
                callback.message.text + "\n\n✅ <b>Подтверждено</b>",
                parse_mode="HTML",
            )
    await callback.answer("Запись подтверждена!")


@router.callback_query(F.data.startswith("reject_"))
async def reject_booking(callback: CallbackQuery):
    """Admin rejects a booking."""
    if callback.from_user.id not in settings.get_admin_ids():
        await callback.answer("Нет доступа", show_alert=True)
        return

    try:
        booking_id = int(callback.data.removeprefix("reject_"))
    except ValueError:
        await callback.answer("Ошибка данных", show_alert=True)
        return
    async with async_session() as session:
        svc = BookingService(session)
        booking = await svc.update_status(booking_id, BookingStatus.CANCELLED)
        if booking:
            config = await ConfigService(session).get_all()
            notifier = NotificationService(bot, config)
            await notifier.notify_client_rejected(booking)
            await callback.message.edit_text(
                callback.message.text + "\n\n❌ <b>Отклонено</b>",
                parse_mode="HTML",
            )
    await callback.answer("Запись отклонена")


@router.callback_query(F.data.startswith("client_confirm_"))
async def client_confirm_reminder(callback: CallbackQuery):
    """Client confirms they will come (from reminder)."""
    await callback.answer("Отлично! Ждём вас! 💅", show_alert=True)
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Вы подтвердили визит",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("client_cancel_"))
async def client_cancel_booking(callback: CallbackQuery):
    """Client cancels booking from reminder."""
    try:
        booking_id = int(callback.data.removeprefix("client_cancel_"))
    except ValueError:
        await callback.answer("Ошибка данных", show_alert=True)
        return
    async with async_session() as session:
        svc = BookingService(session)
        booking = await svc.update_status(booking_id, BookingStatus.CANCELLED)
        if booking:
            # Notify admin
            await bot.send_message(
                settings.ADMIN_TELEGRAM_ID,
                f"❌ Клиент {booking.client.first_name} отменил запись на "
                f"{booking.date.strftime('%d.%m')} в {booking.time_start.strftime('%H:%M')}",
            )
    await callback.answer("Запись отменена", show_alert=True)
    await callback.message.edit_text(
        "Запись отменена. Надеюсь увидеть вас в другой раз! 💅"
    )
