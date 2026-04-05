from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.bot import bot
from app.config import settings
from app.database import async_session
from app.models.booking import BookingStatus
from app.services.booking_service import BookingService
from app.services.notification_service import NotificationService

router = Router()


@router.callback_query(F.data.startswith("confirm_"))
async def confirm_booking(callback: CallbackQuery):
    """Admin confirms a booking."""
    if callback.from_user.id != settings.ADMIN_TELEGRAM_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    booking_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        svc = BookingService(session)
        booking = await svc.update_status(booking_id, BookingStatus.CONFIRMED)
        if booking:
            notifier = NotificationService(bot)
            await notifier.notify_client_confirmed(booking)
            await callback.message.edit_text(
                callback.message.text + "\n\n✅ <b>Подтверждено</b>",
                parse_mode="HTML",
            )
    await callback.answer("Запись подтверждена!")


@router.callback_query(F.data.startswith("reject_"))
async def reject_booking(callback: CallbackQuery):
    """Admin rejects a booking."""
    if callback.from_user.id != settings.ADMIN_TELEGRAM_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    booking_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        svc = BookingService(session)
        booking = await svc.update_status(booking_id, BookingStatus.CANCELLED)
        if booking:
            notifier = NotificationService(bot)
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
    booking_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        svc = BookingService(session)
        booking = await svc.update_status(booking_id, BookingStatus.CANCELLED)
        if booking:
            # Notify admin
            notifier = NotificationService(bot)
            await bot.send_message(
                settings.ADMIN_TELEGRAM_ID,
                f"❌ Клиент {booking.client.first_name} отменил запись на "
                f"{booking.date.strftime('%d.%m')} в {booking.time_start.strftime('%H:%M')}",
            )
    await callback.answer("Запись отменена", show_alert=True)
    await callback.message.edit_text(
        "Запись отменена. Надеюсь увидеть вас в другой раз! 💅"
    )
