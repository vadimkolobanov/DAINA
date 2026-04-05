from datetime import date, time

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


class ScheduleDay(BaseModel):
    day_of_week: int
    is_working: bool
    time_start: str  # "HH:MM"
    time_end: str  # "HH:MM"


class ExceptionCreate(BaseModel):
    date: date
    is_day_off: bool = True
    custom_start: str | None = None  # "HH:MM"
    custom_end: str | None = None  # "HH:MM"
    reason: str | None = None


@router.get("")
async def get_schedule(session: AsyncSession = Depends(get_session)):
    svc = ScheduleService(session)
    schedule = await svc.get_weekly_schedule()
    return [
        {
            "day_of_week": s.day_of_week,
            "is_working": s.is_working,
            "time_start": s.time_start.strftime("%H:%M"),
            "time_end": s.time_end.strftime("%H:%M"),
        }
        for s in schedule
    ]


@router.put("/day")
async def update_schedule_day(data: ScheduleDay, session: AsyncSession = Depends(get_session)):
    svc = ScheduleService(session)
    h1, m1 = map(int, data.time_start.split(":"))
    h2, m2 = map(int, data.time_end.split(":"))
    await svc.update_day(data.day_of_week, data.is_working, time(h1, m1), time(h2, m2))
    return {"ok": True}


@router.post("/exception")
async def add_exception(data: ExceptionCreate, session: AsyncSession = Depends(get_session)):
    svc = ScheduleService(session)
    custom_start = None
    custom_end = None
    if data.custom_start:
        h, m = map(int, data.custom_start.split(":"))
        custom_start = time(h, m)
    if data.custom_end:
        h, m = map(int, data.custom_end.split(":"))
        custom_end = time(h, m)
    await svc.add_exception(data.date, data.is_day_off, custom_start, custom_end, data.reason)
    return {"ok": True}


@router.delete("/exception/{target_date}")
async def delete_exception(target_date: date, session: AsyncSession = Depends(get_session)):
    svc = ScheduleService(session)
    await svc.delete_exception(target_date)
    return {"ok": True}


@router.get("/exceptions")
async def get_exceptions(
    start: date, end: date, session: AsyncSession = Depends(get_session)
):
    svc = ScheduleService(session)
    exceptions = await svc.get_exceptions(start, end)
    return [
        {
            "date": e.date.isoformat(),
            "is_day_off": e.is_day_off,
            "custom_start": e.custom_start.strftime("%H:%M") if e.custom_start else None,
            "custom_end": e.custom_end.strftime("%H:%M") if e.custom_end else None,
            "reason": e.reason,
        }
        for e in exceptions
    ]
