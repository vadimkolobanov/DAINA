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
from app.services.waitlist_service import WaitlistService

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
    async with async_session() as session:
        if not await ConfigService(session).is_admin(callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        try:
            booking_id = int(callback.data.removeprefix("confirm_"))
        except ValueError:
            await callback.answer("Ошибка данных", show_alert=True)
            return
        svc = BookingService(session)
        # Check current status to prevent duplicate processing
        from sqlalchemy import select as sa_select
        from app.models.booking import Booking
        existing = await session.execute(sa_select(Booking).where(Booking.id == booking_id))
        existing_booking = existing.scalar_one_or_none()
        if not existing_booking:
            await callback.answer("Запись не найдена", show_alert=True)
            return
        if existing_booking.status != BookingStatus.PENDING:
            await callback.answer("Запись уже обработана", show_alert=True)
            return
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
    async with async_session() as session:
        if not await ConfigService(session).is_admin(callback.from_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        try:
            booking_id = int(callback.data.removeprefix("reject_"))
        except ValueError:
            await callback.answer("Ошибка данных", show_alert=True)
            return
        svc = BookingService(session)
        # Check current status to prevent duplicate processing
        existing = await session.execute(sa_select(Booking).where(Booking.id == booking_id))
        existing_booking = existing.scalar_one_or_none()
        if not existing_booking:
            await callback.answer("Запись не найдена", show_alert=True)
            return
        if existing_booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            await callback.answer("Запись уже обработана", show_alert=True)
            return
        booking = await svc.update_status(booking_id, BookingStatus.CANCELLED)
        if not booking:
            await callback.answer("Запись не найдена", show_alert=True)
            return
        # Release slot and trigger waitlist
        from app.services.slot_service import SlotService
        slot_svc = SlotService(session)
        service_id = await slot_svc.release_slot(booking_id)
        if service_id:
            from app.services.waitlist_service import WaitlistService
            wl_svc = WaitlistService(session)
            entry = await wl_svc.get_next_waiting(service_id)
            if entry:
                await wl_svc.mark_notified(entry.id)
                config_data = await ConfigService(session).get_all()
                notifier_wl = NotificationService(bot, config_data)
                await notifier_wl.notify_waitlist_slot_available(entry)
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
        if not booking:
            await callback.answer("Запись не найдена или уже отменена", show_alert=True)
            return
        # Release slot and trigger waitlist
        from app.services.slot_service import SlotService
        slot_svc = SlotService(session)
        service_id = await slot_svc.release_slot(booking_id)
        if service_id:
            from app.services.waitlist_service import WaitlistService
            wl_svc = WaitlistService(session)
            entry = await wl_svc.get_next_waiting(service_id)
            if entry:
                await wl_svc.mark_notified(entry.id)
                config_data = await ConfigService(session).get_all()
                notifier = NotificationService(bot, config_data)
                await notifier.notify_waitlist_slot_available(entry)
        # Notify all admins
        admin_ids = await ConfigService(session).get_admin_ids()
        text = (
            f"❌ Клиент {booking.client.first_name} отменил запись на "
            f"{booking.date.strftime('%d.%m')} в {booking.time_start.strftime('%H:%M')}"
        )
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, text)
            except Exception:
                pass
    await callback.answer("Запись отменена", show_alert=True)
    await callback.message.edit_text(
        "Запись отменена. Надеюсь увидеть вас в другой раз! 💅"
    )


@router.callback_query(F.data.startswith("waitlist_decline_"))
async def waitlist_decline(callback: CallbackQuery):
    """Client declines waitlist offer."""
    try:
        entry_id = int(callback.data.removeprefix("waitlist_decline_"))
    except ValueError:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    async with async_session() as session:
        wl_svc = WaitlistService(session)
        entry = await wl_svc.decline_offer(entry_id)
        if not entry:
            await callback.answer("Предложение уже недействительно", show_alert=True)
            return

        # Notify next in line
        next_entry = await wl_svc.get_next_waiting(entry.service_id)
        if next_entry:
            await wl_svc.mark_notified(next_entry.id)
            config = await ConfigService(session).get_all()
            notifier = NotificationService(bot, config)
            await notifier.notify_waitlist_slot_available(next_entry)

    await callback.answer("Понятно! Вы удалены из очереди.", show_alert=True)
    await callback.message.edit_text(
        "Вы отказались от предложения. Если передумаете — можете снова встать в очередь через приложение 💅"
    )
