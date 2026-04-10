from __future__ import annotations

from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import require_admin
from app.services.slot_service import SlotService

router = APIRouter(prefix="/api/slots", tags=["slots"])


class SlotCreate(BaseModel):
    service_id: int
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
        raise HTTPException(status_code=400, detail=f"Invalid time format: {value}, expected HH:MM")


def _slot_response(slot) -> dict:
    return {
        "id": slot.id,
        "service_id": slot.service_id,
        "service_name": slot.service.name if slot.service else "",
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
    ts = _parse_time(data.time_start)
    te = _parse_time(data.time_end)
    if ts >= te:
        raise HTTPException(status_code=400, detail="time_start must be before time_end")

    svc = SlotService(session)
    try:
        slot = await svc.create_slot(data.service_id, data.date, ts, te)
    except Exception:
        raise HTTPException(status_code=400, detail="Slot already exists or invalid data")
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
        raise HTTPException(status_code=400, detail="Some slots already exist or invalid data")
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
        raise HTTPException(status_code=404, detail="Slot not found")
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
        raise HTTPException(status_code=400, detail="Slot not found or already booked")
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
        raise HTTPException(status_code=400, detail="Slot not found or not manually booked")
    return _slot_response(slot)
