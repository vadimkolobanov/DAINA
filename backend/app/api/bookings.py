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
from app.services.slot_service import SlotService
from app.services.waitlist_service import WaitlistService

logger = logging.getLogger(__name__)


async def _trigger_waitlist(session: AsyncSession, service_id: int):
    """Notify next waitlisted client when a slot becomes available."""
    try:
        wl_svc = WaitlistService(session)
        entry = await wl_svc.get_next_waiting(service_id)
        if entry:
            await wl_svc.mark_notified(entry.id)
            from app.bot.bot import bot
            config = await ConfigService(session).get_all()
            from app.services.notification_service import NotificationService
            notifier = NotificationService(bot, config)
            await notifier.notify_waitlist_slot_available(entry)
    except Exception:
        logger.exception("Failed to trigger waitlist for service %s", service_id)

MAX_ACTIVE_BOOKINGS = 3

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
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    svc = SlotService(session)
    slots = await svc.get_available_slots(data.date, data.service_id)
    return [{"time": s.time_start.strftime("%H:%M")} for s in slots]


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
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    svc = SlotService(session)
    dates = await svc.get_available_dates(service_id, start, end)
    return dates


@router.post("", response_model=BookingResponse)
async def create_booking(data: BookingCreate, session: AsyncSession = Depends(get_session)):
    # Validate client exists
    client_result = await session.execute(select(Client).where(Client.id == data.client_id))
    if not client_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Check active bookings limit
    from sqlalchemy import func as sqlfunc
    active_count_q = await session.execute(
        select(sqlfunc.count(Booking.id)).where(
            Booking.client_id == data.client_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
    )
    if (active_count_q.scalar() or 0) >= MAX_ACTIVE_BOOKINGS:
        raise HTTPException(
            status_code=400,
            detail=f"Максимум {MAX_ACTIVE_BOOKINGS} активных записей. Отмените существующую запись чтобы создать новую."
        )

    result = await session.execute(select(Service).where(Service.id == data.service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    # Validate date is not in the past
    if data.date < date.today():
        raise HTTPException(status_code=400, detail="Нельзя записаться на прошедшую дату")

    # Validate time format
    try:
        h, m = map(int, data.time.split(":"))
        target_time = time(h, m)
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Неверный формат времени")

    # Validate slot is available
    slot_svc = SlotService(session)
    available_slots = await slot_svc.get_available_slots(data.date, data.service_id)
    matching = [s for s in available_slots if s.time_start == target_time]
    if not matching:
        raise HTTPException(status_code=400, detail="Это время уже недоступно")

    svc = BookingService(session)
    booking = await svc.create_booking(
        data.client_id, data.service_id, data.date, target_time, service.duration_minutes
    )

    # Link booking to slot
    await slot_svc.book_slot(data.service_id, data.date, target_time, booking.id)

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
        raise HTTPException(status_code=400, detail=f"Неверный статус: {status}")
    svc = BookingService(session)
    booking = await svc.update_status(booking_id, booking_status)
    if not booking:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    # Release slot if booking is cancelled
    if booking_status == BookingStatus.CANCELLED:
        slot_svc = SlotService(session)
        service_id = await slot_svc.release_slot(booking_id)
        if service_id:
            await _trigger_waitlist(session, service_id)

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


@router.put("/{booking_id}/cancel")
async def cancel_booking_by_client(
    booking_id: int, client_id: int, session: AsyncSession = Depends(get_session)
):
    """Cancel a booking by the client. Only pending/confirmed bookings can be cancelled."""
    result = await session.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    if booking.client_id != client_id:
        raise HTTPException(status_code=403, detail="Это не ваша запись")
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        raise HTTPException(status_code=400, detail="Эту запись нельзя отменить")

    svc = BookingService(session)
    await svc.update_status(booking_id, BookingStatus.CANCELLED)

    # Release slot and trigger waitlist
    slot_svc = SlotService(session)
    service_id = await slot_svc.release_slot(booking_id)
    if service_id:
        await _trigger_waitlist(session, service_id)

    # Notify admin about cancellation
    try:
        from app.bot.bot import bot
        from app.services.notification_service import NotificationService
        config = await ConfigService(session).get_all()
        notifier = NotificationService(bot, config)
        admin_ids = await ConfigService(session).get_admin_ids()
        for admin_id in admin_ids:
            await bot.send_message(
                admin_id,
                f"❌ Клиент <b>{booking.client.first_name}</b> отменил запись:\n"
                f"📋 {booking.service.name}\n"
                f"📅 {booking.date.strftime('%d.%m.%Y')} в {booking.time_start.strftime('%H:%M')}",
                parse_mode="HTML",
            )
    except Exception:
        logger.exception("Failed to notify admin about client cancellation for booking %s", booking_id)

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
            "service_id": b.service_id,
            "service_name": b.service.name,
            "service_duration": b.service.duration_minutes,
            "date": b.date.isoformat(),
            "time_start": b.time_start.strftime("%H:%M"),
            "time_end": b.time_end.strftime("%H:%M"),
            "status": b.status.value,
            "price": b.service.price,
        }
        for b in bookings
    ]
