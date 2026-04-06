from __future__ import annotations

from datetime import timedelta

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings
from app.models.booking import Booking


class NotificationService:
    def __init__(self, bot: Bot, config: dict[str, str] | None = None):
        self.bot = bot
        self._config = config or {}

    def _get(self, key: str, fallback: str = "") -> str:
        """Get value from dynamic config, fall back to env settings."""
        if self._config.get(key):
            return self._config[key]
        # Fallback to env
        env_map = {
            "studio_address": settings.STUDIO_ADDRESS,
            "studio_map_url": settings.STUDIO_MAP_URL,
            "app_name": settings.APP_NAME,
            "master_name": settings.MASTER_NAME,
        }
        return env_map.get(key, fallback)

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
        address = self._get("studio_address")
        if address:
            text += f"\n📍 {address}"
        text += "\n\nЖду вас! 💅"

        if booking.client.telegram_id:
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
        if booking.client.telegram_id:
            await self.bot.send_message(
                booking.client.telegram_id,
                "К сожалению, выбранное время недоступно 😔\n\n"
                "Пожалуйста, выберите другое время:",
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    async def notify_client_completed(self, booking: Booking, care_tips: str = ""):
        """Notify client that their visit is marked as completed."""
        service = booking.service
        text = (
            f"Спасибо, что были у нас, <b>{booking.client.first_name}</b>! 💅✨\n\n"
            f"📋 {service.name}\n"
            f"📅 {booking.date.strftime('%d.%m.%Y')}\n"
            f"💰 {service.price}₽\n"
        )
        if care_tips:
            tips_formatted = "\n".join(f"  • {line.strip()}" for line in care_tips.strip().split("\n") if line.strip())
            text += f"\n<b>Советы по уходу:</b>\n{tips_formatted}\n"
        text += "\nБудем рады видеть вас снова!"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📅 Записаться снова", web_app={"url": settings.WEBAPP_URL})],
            ]
        )
        if booking.client.telegram_id:
            await self.bot.send_message(
                booking.client.telegram_id, text, reply_markup=keyboard, parse_mode="HTML"
            )

    async def notify_client_cancelled(self, booking: Booking):
        """Notify client that their booking was cancelled."""
        service = booking.service
        text = (
            f"К сожалению, ваша запись отменена 😔\n\n"
            f"📋 {service.name}\n"
            f"📅 {booking.date.strftime('%d.%m.%Y')}\n"
            f"🕐 {booking.time_start.strftime('%H:%M')} — {booking.time_end.strftime('%H:%M')}\n\n"
            f"Вы можете записаться на другое время:"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📅 Выбрать другое время", web_app={"url": settings.WEBAPP_URL})],
            ]
        )
        if booking.client.telegram_id:
            await self.bot.send_message(
                booking.client.telegram_id, text, reply_markup=keyboard, parse_mode="HTML"
            )

    async def notify_client_noshow(self, booking: Booking):
        """Gentle message for no-show client."""
        text = (
            f"Мы ждали вас сегодня, но, к сожалению, вы не пришли 😔\n\n"
            f"Если что-то случилось — ничего страшного! "
            f"Вы всегда можете записаться на удобное время 💅"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📅 Записаться", web_app={"url": settings.WEBAPP_URL})],
            ]
        )
        if booking.client.telegram_id:
            await self.bot.send_message(
                booking.client.telegram_id, text, reply_markup=keyboard, parse_mode="HTML"
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
        address = self._get("studio_address")
        if address:
            text += f"\n📍 {address}"

        if booking.client.telegram_id:
            await self.bot.send_message(
                booking.client.telegram_id, text, reply_markup=keyboard, parse_mode="HTML"
            )

    async def send_reminder_2h(self, booking: Booking):
        """Send 2-hour reminder to client."""
        text = f"Через 2 часа ваш маникюр! До встречи 💅"
        address = self._get("studio_address")
        map_url = self._get("studio_map_url")
        if map_url and address:
            text += f"\n\n📍 <a href='{map_url}'>{address}</a>"
        elif address:
            text += f"\n\n📍 {address}"
        if booking.client.telegram_id:
            await self.bot.send_message(
                booking.client.telegram_id, text, parse_mode="HTML"
            )

    async def send_followup(self, booking: Booking):
        """Send follow-up after visit."""
        correction_days = 21
        try:
            val = self._config.get("correction_days", "")
            if val:
                correction_days = int(val)
        except (ValueError, TypeError):
            pass

        correction_date = booking.date + timedelta(days=correction_days)
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
        if booking.client.telegram_id:
            await self.bot.send_message(
                booking.client.telegram_id, text, reply_markup=keyboard, parse_mode="HTML"
            )
