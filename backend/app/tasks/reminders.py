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
        # 24-hour reminders: send for bookings happening 23h45m..24h15m from now
        reminder_24h_start = now + timedelta(hours=24) - timedelta(minutes=15)
        reminder_24h_end = now + timedelta(hours=24) + timedelta(minutes=15)

        # Query bookings on the target date(s)
        target_dates_24h = {reminder_24h_start.date(), reminder_24h_end.date()}
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
                    pass

        # 2-hour reminders: send for bookings happening 1h45m..2h15m from now
        reminder_2h_start = now + timedelta(hours=2) - timedelta(minutes=15)
        reminder_2h_end = now + timedelta(hours=2) + timedelta(minutes=15)

        target_dates_2h = {reminder_2h_start.date(), reminder_2h_end.date()}
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
                    pass

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
