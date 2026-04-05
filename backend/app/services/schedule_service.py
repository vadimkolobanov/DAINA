from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule, ScheduleException


class ScheduleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_weekly_schedule(self) -> list[Schedule]:
        result = await self.session.execute(
            select(Schedule).order_by(Schedule.day_of_week)
        )
        return list(result.scalars().all())

    async def update_day(
        self, day_of_week: int, is_working: bool, time_start: time | None = None, time_end: time | None = None
    ) -> Schedule:
        result = await self.session.execute(
            select(Schedule).where(Schedule.day_of_week == day_of_week)
        )
        schedule = result.scalar_one_or_none()
        if schedule:
            schedule.is_working = is_working
            if time_start:
                schedule.time_start = time_start
            if time_end:
                schedule.time_end = time_end
        else:
            schedule = Schedule(
                day_of_week=day_of_week,
                is_working=is_working,
                time_start=time_start or time(10, 0),
                time_end=time_end or time(20, 0),
            )
            self.session.add(schedule)
        await self.session.commit()
        return schedule

    async def add_exception(
        self,
        target_date: date,
        is_day_off: bool = True,
        custom_start: time | None = None,
        custom_end: time | None = None,
        reason: str | None = None,
    ) -> ScheduleException:
        result = await self.session.execute(
            select(ScheduleException).where(ScheduleException.date == target_date)
        )
        exc = result.scalar_one_or_none()
        if exc:
            exc.is_day_off = is_day_off
            exc.custom_start = custom_start
            exc.custom_end = custom_end
            exc.reason = reason
        else:
            exc = ScheduleException(
                date=target_date,
                is_day_off=is_day_off,
                custom_start=custom_start,
                custom_end=custom_end,
                reason=reason,
            )
            self.session.add(exc)
        await self.session.commit()
        return exc

    async def delete_exception(self, target_date: date) -> bool:
        result = await self.session.execute(
            select(ScheduleException).where(ScheduleException.date == target_date)
        )
        exc = result.scalar_one_or_none()
        if exc:
            await self.session.delete(exc)
            await self.session.commit()
            return True
        return False

    async def get_exceptions(self, start: date, end: date) -> list[ScheduleException]:
        result = await self.session.execute(
            select(ScheduleException).where(
                ScheduleException.date.between(start, end)
            )
        )
        return list(result.scalars().all())

    async def init_default_schedule(self):
        """Initialize default weekly schedule if empty."""
        existing = await self.get_weekly_schedule()
        if existing:
            return

        defaults = [
            (0, True, time(10, 0), time(20, 0)),   # Mon
            (1, True, time(10, 0), time(20, 0)),   # Tue
            (2, True, time(10, 0), time(20, 0)),   # Wed
            (3, False, time(10, 0), time(20, 0)),  # Thu - day off
            (4, True, time(10, 0), time(20, 0)),   # Fri
            (5, True, time(10, 0), time(18, 0)),   # Sat
            (6, False, time(10, 0), time(20, 0)),  # Sun - day off
        ]
        for dow, working, start, end in defaults:
            self.session.add(
                Schedule(day_of_week=dow, is_working=working, time_start=start, time_end=end)
            )
        await self.session.commit()
