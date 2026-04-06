from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.client import Client
from app.models.schedule import Schedule, ScheduleException
from app.models.service import Service


class BookingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_available_slots(
        self, target_date: date, duration_minutes: int
    ) -> list[time]:
        """Get available time slots for a given date and service duration."""
        # Check if it's a day off (exception)
        exc = await self.session.execute(
            select(ScheduleException).where(ScheduleException.date == target_date)
        )
        exception = exc.scalar_one_or_none()
        if exception and exception.is_day_off:
            return []

        # Get working hours
        if exception and exception.custom_start and exception.custom_end:
            work_start = exception.custom_start
            work_end = exception.custom_end
        else:
            day_of_week = target_date.weekday()
            sched = await self.session.execute(
                select(Schedule).where(
                    and_(Schedule.day_of_week == day_of_week, Schedule.is_working == True)
                )
            )
            schedule = sched.scalar_one_or_none()
            if not schedule:
                return []
            work_start = schedule.time_start
            work_end = schedule.time_end

        # Get existing bookings for that date
        result = await self.session.execute(
            select(Booking).where(
                and_(
                    Booking.date == target_date,
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                )
            )
        )
        bookings = result.scalars().all()
        booked_ranges = [(b.time_start, b.time_end) for b in bookings]

        # Generate slots every 30 minutes
        slots = []
        current = datetime.combine(target_date, work_start)
        end_dt = datetime.combine(target_date, work_end)
        duration = timedelta(minutes=duration_minutes)
        step = timedelta(minutes=30)

        while current + duration <= end_dt:
            slot_start = current.time()
            slot_end = (current + duration).time()

            # Check overlap with existing bookings
            is_free = True
            for bs, be in booked_ranges:
                if slot_start < be and slot_end > bs:
                    is_free = False
                    break

            if is_free:
                slots.append(slot_start)
            current += step

        return slots

    async def get_available_dates(
        self, start_date: date, end_date: date, duration_minutes: int
    ) -> list[dict]:
        """Get date availability info for a range."""
        dates = []
        current = start_date
        while current <= end_date:
            slots = await self.get_available_slots(current, duration_minutes)
            dates.append(
                {
                    "date": current.isoformat(),
                    "available": len(slots) > 0,
                    "slots_count": len(slots),
                }
            )
            current += timedelta(days=1)
        return dates

    async def create_booking(
        self, client_id: int, service_id: int, target_date: date, target_time: time, duration_minutes: int
    ) -> Booking:
        """Create a new booking."""
        end_time = (
            datetime.combine(target_date, target_time) + timedelta(minutes=duration_minutes)
        ).time()

        booking = Booking(
            client_id=client_id,
            service_id=service_id,
            date=target_date,
            time_start=target_time,
            time_end=end_time,
            status=BookingStatus.PENDING,
        )
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def update_status(self, booking_id: int, status: BookingStatus) -> Booking | None:
        result = await self.session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if not booking:
            return None

        old_status = booking.status
        booking.status = status

        # Update client stats when booking is completed
        if status == BookingStatus.COMPLETED and old_status != BookingStatus.COMPLETED:
            client_result = await self.session.execute(
                select(Client).where(Client.id == booking.client_id)
            )
            client = client_result.scalar_one_or_none()
            if client:
                service_result = await self.session.execute(
                    select(Service).where(Service.id == booking.service_id)
                )
                service = service_result.scalar_one_or_none()
                client.visit_count += 1
                client.total_spent += service.price if service else 0
                client.last_visit_at = datetime.now()

        # Reverse client stats if un-completing a booking
        if old_status == BookingStatus.COMPLETED and status != BookingStatus.COMPLETED:
            client_result = await self.session.execute(
                select(Client).where(Client.id == booking.client_id)
            )
            client = client_result.scalar_one_or_none()
            if client:
                service_result = await self.session.execute(
                    select(Service).where(Service.id == booking.service_id)
                )
                service = service_result.scalar_one_or_none()
                client.visit_count = max(0, client.visit_count - 1)
                client.total_spent = max(0, client.total_spent - (service.price if service else 0))

        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def get_bookings_by_date(self, target_date: date) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.date == target_date)
            .order_by(Booking.time_start)
        )
        return list(result.scalars().all())

    async def get_client_bookings(self, client_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.client_id == client_id)
            .order_by(Booking.date.desc(), Booking.time_start.desc())
        )
        return list(result.scalars().all())
