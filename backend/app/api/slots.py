from __future__ import annotations

from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from app.database import get_session
from app.dependencies import require_admin
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
            from app.services.config_service import ConfigService
            from app.services.notification_service import NotificationService
            config = await ConfigService(session).get_all()
            notifier = NotificationService(bot, config)
            await notifier.notify_waitlist_slot_available(entry)
    except Exception:
        logger.exception("Failed to trigger waitlist for service %s", service_id)

router = APIRouter(prefix="/api/slots", tags=["slots"])


class SlotCreate(BaseModel):
    service_id: int | None = None  # None = universal slot (all services)
    date: date
    time_start: str  # "HH:MM"
    time_end: str  # "HH:MM"


class SlotBatchCreate(BaseModel):
    slots: list[SlotCreate]


class ManualBookRequest(BaseModel):
    client_name: str
    note: str | None = None


def _parse_time(value: str) -> time:
    try:
        h, m = map(int, value.split(":"))
        return time(h, m)
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail=f"Неверный формат времени: {value}")


def _slot_response(slot) -> dict:
    return {
        "id": slot.id,
        "service_id": slot.service_id,
        "service_name": slot.service.name if slot.service else "Все услуги",
        "date": slot.date.isoformat(),
        "time_start": slot.time_start.strftime("%H:%M"),
        "time_end": slot.time_end.strftime("%H:%M"),
        "is_booked": slot.is_booked,
        "booking_id": slot.booking_id,
        "is_manual_booking": slot.is_manual_booking,
        "manual_client_name": slot.manual_client_name,
        "manual_note": slot.manual_note,
        "client_name": (
            f"{slot.booking.client.first_name} {slot.booking.client.last_name or ''}".strip()
            if slot.booking and slot.booking.client
            else slot.manual_client_name
        ),
    }


@router.post("")
async def create_slot(
    data: SlotCreate,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    from datetime import date as date_type
    if data.date < date_type.today():
        raise HTTPException(status_code=400, detail="Нельзя создать окошко на прошедшую дату")
    ts = _parse_time(data.time_start)
    te = _parse_time(data.time_end)
    if ts >= te:
        raise HTTPException(status_code=400, detail="Время начала должно быть раньше времени окончания")

    svc = SlotService(session)
    try:
        slot = await svc.create_slot(data.service_id, data.date, ts, te)
    except Exception:
        raise HTTPException(status_code=400, detail="Окошко уже существует или данные некорректны")
    await _trigger_waitlist(session, data.service_id)
    return _slot_response(slot)


@router.post("/batch")
async def create_slots_batch(
    data: SlotBatchCreate,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    parsed = []
    for s in data.slots:
        ts = _parse_time(s.time_start)
        te = _parse_time(s.time_end)
        if ts >= te:
            raise HTTPException(status_code=400, detail=f"time_start must be before time_end for slot at {s.time_start}")
        parsed.append({
            "service_id": s.service_id,
            "date": s.date,
            "time_start": ts,
            "time_end": te,
        })

    svc = SlotService(session)
    try:
        slots = await svc.create_slots_batch(parsed)
    except Exception:
        raise HTTPException(status_code=400, detail="Некоторые окошки уже существуют или данные некорректны")
    # Trigger waitlist for each unique service
    notified_services = set()
    for s in slots:
        if s.service_id not in notified_services:
            await _trigger_waitlist(session, s.service_id)
            notified_services.add(s.service_id)
    return [_slot_response(s) for s in slots]


@router.delete("/{slot_id}")
async def delete_slot(
    slot_id: int,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = SlotService(session)
    try:
        ok = await svc.delete_slot(slot_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Окошко не найдено")
    return {"ok": True}


@router.get("")
async def get_slots_by_date(
    date: date,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = SlotService(session)
    slots = await svc.get_slots_by_date(date)
    return [_slot_response(s) for s in slots]


@router.get("/dates")
async def get_slot_dates(
    start: date,
    end: date,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = SlotService(session)
    return await svc.get_slot_dates_summary(start, end)


@router.post("/{slot_id}/manual-book")
async def manual_book_slot(
    slot_id: int,
    data: ManualBookRequest,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = SlotService(session)
    slot = await svc.manual_book_slot(slot_id, data.client_name, data.note)
    if not slot:
        raise HTTPException(status_code=400, detail="Окошко не найдено или уже занято")
    return _slot_response(slot)


@router.put("/{slot_id}/manual-book")
async def update_manual_book(
    slot_id: int,
    data: ManualBookRequest,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """Update client name and note on a manually booked slot."""
    from app.models.manual_slot import ManualSlot as MS
    result = await session.execute(
        select(MS).where(MS.id == slot_id, MS.is_manual_booking == True)
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=400, detail="Ручная бронь не найдена")
    slot.manual_client_name = data.client_name
    slot.manual_note = data.note
    await session.commit()
    await session.refresh(slot)
    return _slot_response(slot)


@router.post("/{slot_id}/manual-unbook")
async def manual_unbook_slot(
    slot_id: int,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = SlotService(session)
    slot = await svc.manual_unbook_slot(slot_id)
    if not slot:
        raise HTTPException(status_code=400, detail="Окошко не найдено или не является ручной бронью")
    await _trigger_waitlist(session, slot.service_id)
    return _slot_response(slot)
