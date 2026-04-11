from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import func, select

from app.database import get_session
from app.dependencies import get_current_telegram_user, require_admin
from app.models.booking import Booking, BookingStatus
from app.models.client import Client
from app.services.waitlist_service import WaitlistService

MAX_ACTIVE_BOOKINGS = 3

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/waitlist", tags=["waitlist"])


class WaitlistJoin(BaseModel):
    service_id: int


@router.post("")
async def join_waitlist(
    data: WaitlistJoin,
    telegram_id: int | None = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    # Find client by telegram_id
    result = await session.execute(
        select(Client).where(Client.telegram_id == telegram_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    if client.is_banned:
        raise HTTPException(status_code=403, detail="Доступ ограничен")

    # Check active bookings limit — don't add to waitlist if they can't book anyway
    active_count = await session.execute(
        select(func.count(Booking.id)).where(
            Booking.client_id == client.id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
    )
    if (active_count.scalar() or 0) >= MAX_ACTIVE_BOOKINGS:
        raise HTTPException(
            status_code=400,
            detail=f"У вас уже {MAX_ACTIVE_BOOKINGS} активных записей. Отмените одну, чтобы встать в очередь."
        )

    svc = WaitlistService(session)
    try:
        entry = await svc.add_to_waitlist(client.id, data.service_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Вы уже в очереди ожидания")

    position = await svc.get_waitlist_position(client.id, data.service_id)
    return {"ok": True, "position": position, "waitlist_id": entry.id}


@router.delete("/{service_id}")
async def leave_waitlist(
    service_id: int,
    telegram_id: int | None = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    result = await session.execute(
        select(Client).where(Client.telegram_id == telegram_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    svc = WaitlistService(session)
    ok = await svc.remove_from_waitlist(client.id, service_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Вы не в очереди ожидания")
    return {"ok": True}


@router.get("/position/{service_id}")
async def get_position(
    service_id: int,
    telegram_id: int | None = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
):
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    result = await session.execute(
        select(Client).where(Client.telegram_id == telegram_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        return {"in_waitlist": False, "position": None}

    svc = WaitlistService(session)
    position = await svc.get_waitlist_position(client.id, service_id)
    return {
        "in_waitlist": position is not None,
        "position": position,
    }


@router.get("/service/{service_id}")
async def get_service_waitlist(
    service_id: int,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = WaitlistService(session)
    entries = await svc.get_service_waitlist(service_id)
    return [
        {
            "id": e.id,
            "client_id": e.client_id,
            "client_name": f"{e.client.first_name} {e.client.last_name or ''}".strip(),
            "service_name": e.service.name,
            "status": e.status.value,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "notified_at": e.notified_at.isoformat() if e.notified_at else None,
        }
        for e in entries
    ]
