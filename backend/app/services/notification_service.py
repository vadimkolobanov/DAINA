from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings
from app.models.booking import Booking


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_admin_new_booking(self, booking: Booking):
        """Notify master about new booking."""
        client = booking.client
        service = booking.service
        is_new = client.visit_count == 0

        text = (
            f"🆕 <b>Новая запись!</b>\n\n"
            f"👤 {client.first_name} {client.last_name or ''}"
        )
        if client.instagram_handle:
            text += f" (@{client.instagram_handle})"
        text += (
            f"\n📋 {service.name}\n"
            f"📅 {booking.date.strftime('%d.%m.%Y')}\n"
            f"🕐 {booking.time_start.strftime('%H:%M')} — {booking.time_end.strftime('%H:%M')}\n"
            f"💰 {service.price}₽"
        )
        if is_new:
            text += "\n\n⚠️ <b>Новый клиент (первый визит)</b>"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{booking.id}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{booking.id}"),
                ],
            ]
        )
        await self.bot.send_message(
            settings.ADMIN_TELEGRAM_ID, text, reply_markup=keyboard, parse_mode="HTML"
        )

    async def notify_client_confirmed(self, booking: Booking):
        """Notify client that booking is confirmed."""
        service = booking.service
        text = (
            f"✅ <b>Ваша запись подтверждена!</b>\n\n"
            f"📋 {service.name}\n"
            f"📅 {booking.date.strftime('%d.%m.%Y')}\n"
            f"🕐 {booking.time_start.strftime('%H:%M')} — {booking.time_end.strftime('%H:%M')}\n"
            f"💰 {service.price}₽\n"
        )
        if settings.STUDIO_ADDRESS:
            text += f"\n📍 {settings.STUDIO_ADDRESS}"
        text += "\n\nЖду вас! 💅"

        await self.bot.send_message(
            booking.client.telegram_id, text, parse_mode="HTML"
        )

    async def notify_client_rejected(self, booking: Booking):
        """Notify client that booking was rejected."""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📅 Выбрать другое время", web_app={"url": settings.WEBAPP_URL})],
            ]
        )
        await self.bot.send_message(
            booking.client.telegram_id,
            "К сожалению, выбранное время недоступно 😔\n\n"
            "Пожалуйста, выберите другое время:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    async def send_reminder_24h(self, booking: Booking):
        """Send 24-hour reminder to client."""
        service = booking.service
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"client_confirm_{booking.id}"),
                    InlineKeyboardButton(text="📅 Перенести", web_app={"url": settings.WEBAPP_URL}),
                ],
                [
                    InlineKeyboardButton(text="❌ Отменить", callback_data=f"client_cancel_{booking.id}"),
                ],
            ]
        )
        text = (
            f"Напоминаю, завтра в {booking.time_start.strftime('%H:%M')} "
            f"вас ждёт {service.name} ✨\n"
        )
        if settings.STUDIO_ADDRESS:
            text += f"\n📍 {settings.STUDIO_ADDRESS}"

        await self.bot.send_message(
            booking.client.telegram_id, text, reply_markup=keyboard, parse_mode="HTML"
        )

    async def send_reminder_2h(self, booking: Booking):
        """Send 2-hour reminder to client."""
        text = f"Через 2 часа ваш маникюр! До встречи 💅"
        if settings.STUDIO_MAP_URL:
            text += f"\n\n📍 <a href='{settings.STUDIO_MAP_URL}'>{settings.STUDIO_ADDRESS}</a>"
        await self.bot.send_message(
            booking.client.telegram_id, text, parse_mode="HTML"
        )

    async def send_followup(self, booking: Booking):
        """Send follow-up after visit."""
        from datetime import timedelta

        correction_date = booking.date + timedelta(days=settings.CORRECTION_DAYS)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📅 Записаться снова", web_app={"url": settings.WEBAPP_URL})],
            ]
        )
        text = (
            f"Спасибо за визит! Надеюсь, вам понравилось ✨\n\n"
            f"Рекомендуемая дата следующего визита: "
            f"~{correction_date.strftime('%d.%m.%Y')}\n\n"
            f"Хотите записаться на следующий раз?"
        )
        await self.bot.send_message(
            booking.client.telegram_id, text, reply_markup=keyboard, parse_mode="HTML"
        )
