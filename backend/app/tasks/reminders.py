from datetime import date, datetime, timedelta

from sqlalchemy import and_, select

from app.bot.bot import bot
from app.database import async_session
from app.models.booking import Booking, BookingStatus
from app.services.notification_service import NotificationService


async def check_reminders():
    """Check and send booking reminders. Run every 15 minutes."""
    now = datetime.now()
    notifier = NotificationService(bot)

    async with async_session() as session:
        # 24-hour reminders
        tomorrow = now + timedelta(hours=24)
        result = await session.execute(
            select(Booking).where(
                and_(
                    Booking.date == tomorrow.date(),
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.reminder_24h_sent == False,
                )
            )
        )
        for booking in result.scalars().all():
            booking_dt = datetime.combine(booking.date, booking.time_start)
            if abs((booking_dt - tomorrow).total_seconds()) < 900:  # within 15 min
                await notifier.send_reminder_24h(booking)
                booking.reminder_24h_sent = True

        # 2-hour reminders
        in_2h = now + timedelta(hours=2)
        result = await session.execute(
            select(Booking).where(
                and_(
                    Booking.date == in_2h.date(),
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.reminder_2h_sent == False,
                )
            )
        )
        for booking in result.scalars().all():
            booking_dt = datetime.combine(booking.date, booking.time_start)
            if abs((booking_dt - in_2h).total_seconds()) < 900:
                await notifier.send_reminder_2h(booking)
                booking.reminder_2h_sent = True

        await session.commit()


async def check_followups():
    """Check and send post-visit follow-ups. Run every 30 minutes."""
    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)
    notifier = NotificationService(bot)

    async with async_session() as session:
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
                await notifier.send_followup(booking)
                booking.followup_sent = True

        await session.commit()
