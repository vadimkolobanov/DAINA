from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.booking import Booking, BookingStatus
from app.models.service import Service
from app.services.booking_service import BookingService

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


class AvailableSlotsRequest(BaseModel):
    date: date
    service_id: int


class BookingCreate(BaseModel):
    client_id: int
    service_id: int
    date: date
    time: str  # "HH:MM"


class BookingResponse(BaseModel):
    id: int
    client_id: int
    service_id: int
    date: date
    time_start: time
    time_end: time
    status: BookingStatus
    created_at: datetime | None = None
    client_name: str | None = None
    service_name: str | None = None

    model_config = {"from_attributes": True}


class DateAvailability(BaseModel):
    date: str
    available: bool
    slots_count: int


@router.post("/available-slots")
async def get_available_slots(
    data: AvailableSlotsRequest, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Service).where(Service.id == data.service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    svc = BookingService(session)
    slots = await svc.get_available_slots(data.date, service.duration_minutes)
    return [{"time": s.strftime("%H:%M")} for s in slots]


@router.get("/available-dates")
async def get_available_dates(
    service_id: int,
    start: date,
    end: date,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    svc = BookingService(session)
    dates = await svc.get_available_dates(start, end, service.duration_minutes)
    return dates


@router.post("", response_model=BookingResponse)
async def create_booking(data: BookingCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Service).where(Service.id == data.service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    h, m = map(int, data.time.split(":"))
    target_time = time(h, m)

    svc = BookingService(session)
    slots = await svc.get_available_slots(data.date, service.duration_minutes)
    if target_time not in slots:
        raise HTTPException(status_code=400, detail="Time slot not available")

    booking = await svc.create_booking(
        data.client_id, data.service_id, data.date, target_time, service.duration_minutes
    )

    # Notify master about new booking
    try:
        from app.bot.bot import bot
        from app.services.notification_service import NotificationService
        notifier = NotificationService(bot)
        await notifier.notify_admin_new_booking(booking)
    except Exception:
        pass  # Don't fail booking if notification fails

    return booking


@router.put("/{booking_id}/status")
async def update_booking_status(
    booking_id: int, status: str, session: AsyncSession = Depends(get_session)
):
    svc = BookingService(session)
    booking = await svc.update_status(booking_id, BookingStatus(status))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"ok": True}


@router.get("/by-date/{target_date}")
async def get_bookings_by_date(
    target_date: date, session: AsyncSession = Depends(get_session)
):
    svc = BookingService(session)
    bookings = await svc.get_bookings_by_date(target_date)
    return [
        {
            "id": b.id,
            "client_id": b.client_id,
            "client_name": f"{b.client.first_name} {b.client.last_name or ''}".strip(),
            "client_instagram": b.client.instagram_handle,
            "client_visit_count": b.client.visit_count,
            "service_name": b.service.name,
            "service_id": b.service_id,
            "date": b.date.isoformat(),
            "time_start": b.time_start.strftime("%H:%M"),
            "time_end": b.time_end.strftime("%H:%M"),
            "status": b.status.value,
            "price": b.service.price,
        }
        for b in bookings
    ]


@router.get("/client/{client_id}")
async def get_client_bookings(client_id: int, session: AsyncSession = Depends(get_session)):
    svc = BookingService(session)
    bookings = await svc.get_client_bookings(client_id)
    return [
        {
            "id": b.id,
            "service_name": b.service.name,
            "date": b.date.isoformat(),
            "time_start": b.time_start.strftime("%H:%M"),
            "time_end": b.time_end.strftime("%H:%M"),
            "status": b.status.value,
            "price": b.service.price,
        }
        for b in bookings
    ]
