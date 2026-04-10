from __future__ import annotations

from datetime import timedelta

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import settings
from app.models.booking import Booking
from app.models.client import Client


def _cabinet_kb(extra_rows: list[list[InlineKeyboardButton]] | None = None) -> InlineKeyboardMarkup:
    """Build keyboard with optional extra rows + always-present cabinet button."""
    rows = list(extra_rows or [])
    rows.append([InlineKeyboardButton(text="💅 Открыть личный кабинет", web_app=WebAppInfo(url=settings.WEBAPP_URL))])
    return InlineKeyboardMarkup(inline_keyboard=rows)


class NotificationService:
    def __init__(self, bot: Bot, config: dict[str, str] | None = None):
        self.bot = bot
        self._config = config or {}

    def _get(self, key: str, fallback: str = "") -> str:
        return self._config.get(key) or fallback

    @property
    def currency(self) -> str:
        return self._get("currency", "руб")

    def _get_admin_ids(self) -> set[int]:
        """Get all admin IDs from config dict + bootstrap env admin."""
        ids: set[int] = set()
        if settings.ADMIN_TELEGRAM_ID:
            ids.add(settings.ADMIN_TELEGRAM_ID)
        raw_ids = self._config.get("admin_ids", "")
        if raw_ids:
            for raw in raw_ids.split(","):
                raw = raw.strip()
                if raw.isdigit():
                    ids.add(int(raw))
        return ids

    async def _send_client(self, telegram_id: int | None, text: str, keyboard: InlineKeyboardMarkup | None = None):
        """Send message to client if they have telegram_id."""
        if not telegram_id:
            return
        await self.bot.send_message(telegram_id, text, reply_markup=keyboard, parse_mode="HTML")

    # ── Admin notifications ──

    async def notify_admin_new_booking(self, booking: Booking):
        client = booking.client
        service = booking.service
        is_new = client.visit_count == 0

        text = f"🆕 <b>Новая запись!</b>\n\n👤 {client.first_name} {client.last_name or ''}\n"
        if client.phone:
            text += f"📞 {client.phone}\n"
        if client.instagram_handle:
            text += f"📷 Instagram: @{client.instagram_handle}\n"
        if client.username:
            text += f"✈️ Telegram: @{client.username}\n"
        text += (
            f"\n📋 {service.name}\n"
            f"📅 {booking.date.strftime('%d.%m.%Y')}\n"
            f"🕐 {booking.time_start.strftime('%H:%M')} — {booking.time_end.strftime('%H:%M')}\n"
            f"💰 {service.price} {self.currency}"
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
        # Send to all configured admins (DB config + bootstrap env admin)
        admin_ids = self._get_admin_ids()
        for admin_id in admin_ids:
            try:
                await self.bot.send_message(
                    admin_id, text, reply_markup=keyboard, parse_mode="HTML"
                )
            except Exception:
                pass

    # ── Client booking notifications ──

    async def notify_client_confirmed(self, booking: Booking):
        service = booking.service
        text = (
            f"✅ <b>Запись подтверждена!</b>\n\n"
            f"📋 {service.name}\n"
            f"📅 {booking.date.strftime('%d.%m.%Y')}\n"
            f"🕐 {booking.time_start.strftime('%H:%M')} — {booking.time_end.strftime('%H:%M')}\n"
            f"💰 {service.price} {self.currency}\n"
        )
        address = self._get("studio_address")
        if address:
            text += f"\n📍 {address}"
        text += "\n\nЖду вас! 💅"

        await self._send_client(booking.client.telegram_id, text, _cabinet_kb())

    async def notify_client_rejected(self, booking: Booking):
        text = (
            "К сожалению, выбранное время недоступно 😔\n\n"
            "Пожалуйста, выберите другое время:"
        )
        await self._send_client(booking.client.telegram_id, text, _cabinet_kb())

    async def notify_client_completed(self, booking: Booking, care_tips: str = ""):
        service = booking.service
        text = (
            f"Спасибо за визит, <b>{booking.client.first_name}</b>! 💅✨\n\n"
            f"📋 {service.name}\n"
            f"📅 {booking.date.strftime('%d.%m.%Y')}\n"
            f"💰 {service.price} {self.currency}\n"
        )
        if care_tips:
            tips = "\n".join(f"  • {l.strip()}" for l in care_tips.strip().split("\n") if l.strip())
            text += f"\n<b>Советы по уходу:</b>\n{tips}\n"
        text += "\nБуду рада видеть вас снова!"

        await self._send_client(booking.client.telegram_id, text, _cabinet_kb())

    async def notify_client_cancelled(self, booking: Booking):
        service = booking.service
        text = (
            f"К сожалению, запись отменена 😔\n\n"
            f"📋 {service.name}\n"
            f"📅 {booking.date.strftime('%d.%m.%Y')}\n"
            f"🕐 {booking.time_start.strftime('%H:%M')} — {booking.time_end.strftime('%H:%M')}\n\n"
            f"Вы можете записаться на другое время:"
        )
        await self._send_client(booking.client.telegram_id, text, _cabinet_kb())

    async def notify_client_noshow(self, booking: Booking):
        text = (
            f"Я ждала вас сегодня, но, к сожалению, вы не пришли 😔\n\n"
            f"Если что-то случилось — ничего страшного! "
            f"Вы всегда можете записаться на удобное время 💅"
        )
        await self._send_client(booking.client.telegram_id, text, _cabinet_kb())

    # ── VIP notification ──

    async def notify_client_vip(self, client: Client):
        vip_text = self._config.get("vip_message", "") or (
            "Вам присвоен VIP-статус! 💎\n"
            "Теперь вы в числе особенных клиентов.\n"
            "Спасибо за доверие!"
        )
        text = f"✨ <b>{client.first_name}</b>, у меня для вас отличная новость!\n\n{vip_text}"
        await self._send_client(client.telegram_id, text, _cabinet_kb())

    # ── Reminders ──

    async def send_reminder_24h(self, booking: Booking):
        service = booking.service
        text = (
            f"Напоминаю, завтра в {booking.time_start.strftime('%H:%M')} "
            f"вас ждёт {service.name} ✨\n"
        )
        address = self._get("studio_address")
        if address:
            text += f"\n📍 {address}"

        keyboard = _cabinet_kb([
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"client_confirm_{booking.id}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"client_cancel_{booking.id}"),
            ],
        ])
        await self._send_client(booking.client.telegram_id, text, keyboard)

    async def send_reminder_2h(self, booking: Booking):
        text = f"Через 2 часа ваш маникюр! До встречи 💅"
        address = self._get("studio_address")
        map_url = self._get("studio_map_url")
        if map_url and address:
            text += f"\n\n📍 <a href='{map_url}'>{address}</a>"
        elif address:
            text += f"\n\n📍 {address}"
        await self._send_client(booking.client.telegram_id, text, _cabinet_kb())

    async def send_followup(self, booking: Booking):
        correction_days = 21
        try:
            val = self._config.get("correction_days", "")
            if val:
                correction_days = int(val)
        except (ValueError, TypeError):
            pass

        correction_date = booking.date + timedelta(days=correction_days)
        text = (
            f"Спасибо за визит! Надеюсь, вам понравилось ✨\n\n"
            f"Рекомендуемая дата следующего визита: "
            f"~{correction_date.strftime('%d.%m.%Y')}\n\n"
            f"Хотите записаться?"
        )
        await self._send_client(booking.client.telegram_id, text, _cabinet_kb())
