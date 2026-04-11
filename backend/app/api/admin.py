from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import require_admin
from app.models.booking import Booking, BookingStatus
from app.models.client import Client
from app.models.client_photo import ClientPhoto
from app.models.manual_slot import ManualSlot
from app.models.service import Service
from app.models.waitlist import WaitlistEntry

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
async def get_stats(
    period: str = "month",  # month, week, all
    session: AsyncSession = Depends(get_session),
):
    today = date.today()
    if period == "week":
        start = today - timedelta(days=today.weekday())
    elif period == "month":
        start = today.replace(day=1)
    else:
        start = date(2020, 1, 1)

    start_dt = datetime.combine(start, datetime.min.time())

    # Total bookings
    total_q = await session.execute(
        select(func.count(Booking.id)).where(Booking.date >= start)
    )
    total = total_q.scalar() or 0

    # By status
    completed_q = await session.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.date >= start, Booking.status == BookingStatus.COMPLETED)
        )
    )
    completed = completed_q.scalar() or 0

    confirmed_q = await session.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.date >= start, Booking.status == BookingStatus.CONFIRMED)
        )
    )
    confirmed = confirmed_q.scalar() or 0

    pending_q = await session.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.date >= start, Booking.status == BookingStatus.PENDING)
        )
    )
    pending = pending_q.scalar() or 0

    cancelled_q = await session.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.date >= start, Booking.status == BookingStatus.CANCELLED)
        )
    )
    cancelled = cancelled_q.scalar() or 0

    noshow_q = await session.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.date >= start, Booking.status == BookingStatus.NO_SHOW)
        )
    )
    no_show = noshow_q.scalar() or 0

    # Revenue — from completed + confirmed + pending (all non-cancelled)
    active_statuses = [BookingStatus.COMPLETED, BookingStatus.CONFIRMED, BookingStatus.PENDING]
    revenue_q = await session.execute(
        select(func.sum(Service.price))
        .join(Booking, Booking.service_id == Service.id)
        .where(and_(Booking.date >= start, Booking.status.in_(active_statuses)))
    )
    revenue = revenue_q.scalar() or 0

    active_count = completed + confirmed + pending

    # New clients
    new_clients_q = await session.execute(
        select(func.count(Client.id)).where(Client.created_at >= start_dt)
    )
    new_clients = new_clients_q.scalar() or 0

    # Total clients
    total_clients_q = await session.execute(select(func.count(Client.id)))
    total_clients = total_clients_q.scalar() or 0

    # Manual bookings (from manual_slots)
    manual_count_q = await session.execute(
        select(func.count(ManualSlot.id)).where(
            ManualSlot.date >= start,
            ManualSlot.is_manual_booking == True,
        )
    )
    manual_count = manual_count_q.scalar() or 0

    # Manual revenue
    manual_revenue_q = await session.execute(
        select(func.sum(Service.price))
        .join(ManualSlot, ManualSlot.service_id == Service.id)
        .where(
            ManualSlot.date >= start,
            ManualSlot.is_manual_booking == True,
        )
    )
    manual_revenue = manual_revenue_q.scalar() or 0

    total_with_manual = total + manual_count
    revenue_with_manual = revenue + manual_revenue

    return {
        "period": period,
        "start_date": start.isoformat(),
        "total_bookings": total_with_manual,
        "pending": pending,
        "confirmed": confirmed,
        "completed": completed,
        "cancelled": cancelled,
        "no_show": no_show,
        "revenue": revenue_with_manual,
        "average_check": revenue_with_manual // total_with_manual if total_with_manual > 0 else 0,
        "new_clients": new_clients,
        "total_clients": total_clients,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
        "manual_bookings": manual_count,
    }


@router.get("/dashboard")
async def get_dashboard(
    target_date: date | None = None,
    session: AsyncSession = Depends(get_session),
):
    from app.services.booking_service import BookingService

    day = target_date or date.today()
    svc = BookingService(session)
    bookings = await svc.get_bookings_by_date(day)

    booking_items = [
        {
            "id": b.id,
            "client_id": b.client.id,
            "client_name": f"{b.client.first_name} {b.client.last_name or ''}".strip(),
            "client_instagram": b.client.instagram_handle,
            "client_is_new": b.client.visit_count == 0,
            "client_telegram_id": b.client.telegram_id,
            "service_name": b.service.name,
            "time_start": b.time_start.strftime("%H:%M"),
            "time_end": b.time_end.strftime("%H:%M"),
            "status": b.status.value,
            "price": b.service.price,
            "is_manual": False,
        }
        for b in bookings
    ]

    # Add manual bookings from manual_slots
    manual_result = await session.execute(
        select(ManualSlot).where(
            ManualSlot.date == day,
            ManualSlot.is_manual_booking == True,
        ).order_by(ManualSlot.time_start)
    )
    for slot in manual_result.scalars().all():
        booking_items.append({
            "id": f"manual_{slot.id}",
            "client_id": None,
            "client_name": slot.manual_client_name or "Личная запись",
            "client_instagram": None,
            "client_is_new": False,
            "client_telegram_id": None,
            "service_name": slot.service.name if slot.service else "Все услуги",
            "time_start": slot.time_start.strftime("%H:%M"),
            "time_end": slot.time_end.strftime("%H:%M"),
            "status": "confirmed",
            "price": slot.service.price if slot.service else 0,
            "is_manual": True,
            "manual_note": slot.manual_note,
        })

    # Sort all by time
    booking_items.sort(key=lambda x: x["time_start"])

    return {
        "date": day.isoformat(),
        "bookings_count": len(booking_items),
        "bookings": booking_items,
    }


@router.get("/all-bookings")
async def get_all_bookings(
    start: date | None = None,
    end: date | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Booking).order_by(Booking.date.desc(), Booking.time_start.desc())
    if start:
        stmt = stmt.where(Booking.date >= start)
    if end:
        stmt = stmt.where(Booking.date <= end)
    if status:
        try:
            stmt = stmt.where(Booking.status == BookingStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Неверный статус: {status}")

    result = await session.execute(stmt)
    bookings = result.scalars().all()

    return [
        {
            "id": b.id,
            "client_id": b.client.id,
            "client_name": f"{b.client.first_name} {b.client.last_name or ''}".strip(),
            "client_instagram": b.client.instagram_handle,
            "service_name": b.service.name,
            "date": b.date.isoformat(),
            "time_start": b.time_start.strftime("%H:%M"),
            "time_end": b.time_end.strftime("%H:%M"),
            "status": b.status.value,
            "price": b.service.price,
        }
        for b in bookings
    ]


@router.delete("/booking/{booking_id}")
async def delete_booking(booking_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    # Unlink any manual_slot referencing this booking
    linked_slots = await session.execute(
        select(ManualSlot).where(ManualSlot.booking_id == booking_id)
    )
    for slot in linked_slots.scalars().all():
        slot.booking_id = None

    await session.delete(booking)
    await session.commit()
    return {"ok": True}


@router.delete("/client/{client_id}")
async def delete_client(client_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Check for active bookings
    active_q = await session.execute(
        select(func.count(Booking.id)).where(
            Booking.client_id == client_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
    )
    if (active_q.scalar() or 0) > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить клиента с активными записями. Сначала отмените или завершите записи."
        )

    # Delete client's photos first
    photos = await session.execute(
        select(ClientPhoto).where(ClientPhoto.client_id == client_id)
    )
    for p in photos.scalars().all():
        await session.delete(p)

    # Delete client's waitlist entries
    waitlist_entries = await session.execute(
        select(WaitlistEntry).where(WaitlistEntry.client_id == client_id)
    )
    for w in waitlist_entries.scalars().all():
        await session.delete(w)

    # Unlink manual_slots from client's bookings, then delete bookings
    bookings = await session.execute(
        select(Booking).where(Booking.client_id == client_id)
    )
    booking_list = bookings.scalars().all()
    booking_ids = [b.id for b in booking_list]
    if booking_ids:
        linked_slots = await session.execute(
            select(ManualSlot).where(ManualSlot.booking_id.in_(booking_ids))
        )
        for slot in linked_slots.scalars().all():
            slot.booking_id = None
    for b in booking_list:
        await session.delete(b)

    await session.delete(client)
    await session.commit()
    return {"ok": True}
