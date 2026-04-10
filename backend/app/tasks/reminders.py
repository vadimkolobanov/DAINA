import logging
from datetime import date, datetime, timedelta

from sqlalchemy import and_, select

from app.bot.bot import bot
from app.database import async_session
from app.models.booking import Booking, BookingStatus
from app.services.config_service import ConfigService
from app.services.notification_service import NotificationService
from app.services.waitlist_service import WaitlistService

logger = logging.getLogger(__name__)


async def check_reminders():
    """Check and send booking reminders. Run every 15 minutes."""
    now = datetime.now()

    try:
        async with async_session() as session:
            config = await ConfigService(session).get_all()
            notifier = NotificationService(bot, config)
            # 24-hour reminders: send for bookings happening 23h45m..24h15m from now
            reminder_24h_start = now + timedelta(hours=24) - timedelta(minutes=15)
            reminder_24h_end = now + timedelta(hours=24) + timedelta(minutes=15)

            # Query bookings on the target date(s) — use sorted list for asyncpg compatibility
            target_dates_24h = sorted(set([reminder_24h_start.date(), reminder_24h_end.date()]))
            result = await session.execute(
                select(Booking).where(
                    and_(
                        Booking.date.in_(target_dates_24h),
                        Booking.status == BookingStatus.CONFIRMED,
                        Booking.reminder_24h_sent == False,
                    )
                )
            )
            for booking in result.scalars().all():
                booking_dt = datetime.combine(booking.date, booking.time_start)
                if reminder_24h_start <= booking_dt <= reminder_24h_end:
                    try:
                        await notifier.send_reminder_24h(booking)
                        booking.reminder_24h_sent = True
                    except Exception:
                        logger.exception("Failed to send 24h reminder for booking %s", booking.id)

            # 2-hour reminders: send for bookings happening 1h45m..2h15m from now
            reminder_2h_start = now + timedelta(hours=2) - timedelta(minutes=15)
            reminder_2h_end = now + timedelta(hours=2) + timedelta(minutes=15)

            target_dates_2h = sorted(set([reminder_2h_start.date(), reminder_2h_end.date()]))
            result = await session.execute(
                select(Booking).where(
                    and_(
                        Booking.date.in_(target_dates_2h),
                        Booking.status == BookingStatus.CONFIRMED,
                        Booking.reminder_2h_sent == False,
                    )
                )
            )
            for booking in result.scalars().all():
                booking_dt = datetime.combine(booking.date, booking.time_start)
                if reminder_2h_start <= booking_dt <= reminder_2h_end:
                    try:
                        await notifier.send_reminder_2h(booking)
                        booking.reminder_2h_sent = True
                    except Exception:
                        logger.exception("Failed to send 2h reminder for booking %s", booking.id)

            await session.commit()
    except Exception:
        logger.exception("Error in check_reminders task")


async def check_followups():
    """Check and send post-visit follow-ups. Run every 30 minutes."""
    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)

    try:
        async with async_session() as session:
            config = await ConfigService(session).get_all()
            notifier = NotificationService(bot, config)
            result = await session.execute(
                select(Booking).where(
                    and_(
                        Booking.date == two_hours_ago.date(),
                        Booking.status == BookingStatus.COMPLETED,
                        Booking.followup_sent == False,
                    )
                )
            )
            for booking in result.scalars().all():
                booking_end = datetime.combine(booking.date, booking.time_end)
                if booking_end <= two_hours_ago:
                    try:
                        await notifier.send_followup(booking)
                        booking.followup_sent = True
                    except Exception:
                        logger.exception("Failed to send followup for booking %s", booking.id)

            await session.commit()
    except Exception:
        logger.exception("Error in check_followups task")


async def expire_waitlist_offers():
    """Expire stale waitlist offers and notify next in line. Run every 5 minutes."""
    try:
        async with async_session() as session:
            wl_svc = WaitlistService(session)
            service_ids = await wl_svc.expire_stale_offers()

            if service_ids:
                config = await ConfigService(session).get_all()
                notifier = NotificationService(bot, config)
                for service_id in service_ids:
                    entry = await wl_svc.get_next_waiting(service_id)
                    if entry:
                        await wl_svc.mark_notified(entry.id)
                        await notifier.notify_waitlist_slot_available(entry)
    except Exception:
        logger.exception("Error in expire_waitlist_offers task")
