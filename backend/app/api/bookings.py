from __future__ import annotations

import logging
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.booking import Booking, BookingStatus
from app.models.client import Client
from app.models.service import Service
from app.services.booking_service import BookingService
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)


async def _get_slot_interval(session: AsyncSession) -> int:
    """Get slot interval from config, default 30 min."""
    try:
        config_svc = ConfigService(session)
        val = await config_svc.get("slot_interval")
        return max(10, int(val))
    except (ValueError, TypeError):
        return 30

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

    interval = await _get_slot_interval(session)
    svc = BookingService(session, slot_interval=interval)
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

    interval = await _get_slot_interval(session)
    svc = BookingService(session, slot_interval=interval)
    dates = await svc.get_available_dates(start, end, service.duration_minutes)
    return dates


@router.post("", response_model=BookingResponse)
async def create_booking(data: BookingCreate, session: AsyncSession = Depends(get_session)):
    # Validate client exists
    client_result = await session.execute(select(Client).where(Client.id == data.client_id))
    if not client_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Client not found")

    result = await session.execute(select(Service).where(Service.id == data.service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Validate date is not in the past
    if data.date < date.today():
        raise HTTPException(status_code=400, detail="Cannot book a date in the past")

    # Validate time format
    try:
        h, m = map(int, data.time.split(":"))
        target_time = time(h, m)
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid time format, expected HH:MM")

    interval = await _get_slot_interval(session)
    svc = BookingService(session, slot_interval=interval)
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
        config = await ConfigService(session).get_all()
        notifier = NotificationService(bot, config)
        await notifier.notify_admin_new_booking(booking)
    except Exception:
        logger.exception("Failed to send new booking notification for booking %s", booking.id)

    return booking


@router.put("/{booking_id}/status")
async def update_booking_status(
    booking_id: int, status: str, session: AsyncSession = Depends(get_session)
):
    try:
        booking_status = BookingStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    svc = BookingService(session)
    booking = await svc.update_status(booking_id, booking_status)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Notify client about status change
    try:
        from app.bot.bot import bot
        from app.services.notification_service import NotificationService
        config = await ConfigService(session).get_all()
        notifier = NotificationService(bot, config)

        if booking_status == BookingStatus.CONFIRMED:
            await notifier.notify_client_confirmed(booking)
        elif booking_status == BookingStatus.COMPLETED:
            await notifier.notify_client_completed(booking, config.get("care_tips", ""))
        elif booking_status == BookingStatus.CANCELLED:
            await notifier.notify_client_cancelled(booking)
        elif booking_status == BookingStatus.NO_SHOW:
            await notifier.notify_client_noshow(booking)
    except Exception:
        logger.exception("Failed to notify client about status change for booking %s", booking.id)

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
