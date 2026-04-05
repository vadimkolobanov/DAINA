from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.booking import Booking, BookingStatus
from app.models.client import Client

router = APIRouter(prefix="/api/admin", tags=["admin"])


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

    # Total bookings
    total_q = await session.execute(
        select(func.count(Booking.id)).where(Booking.date >= start)
    )
    total = total_q.scalar() or 0

    # Completed
    completed_q = await session.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.date >= start, Booking.status == BookingStatus.COMPLETED)
        )
    )
    completed = completed_q.scalar() or 0

    # Cancelled
    cancelled_q = await session.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.date >= start, Booking.status == BookingStatus.CANCELLED)
        )
    )
    cancelled = cancelled_q.scalar() or 0

    # No-show
    noshow_q = await session.execute(
        select(func.count(Booking.id)).where(
            and_(Booking.date >= start, Booking.status == BookingStatus.NO_SHOW)
        )
    )
    no_show = noshow_q.scalar() or 0

    # Revenue (from completed bookings)
    from app.models.service import Service

    revenue_q = await session.execute(
        select(func.sum(Service.price))
        .join(Booking, Booking.service_id == Service.id)
        .where(
            and_(Booking.date >= start, Booking.status == BookingStatus.COMPLETED)
        )
    )
    revenue = revenue_q.scalar() or 0

    # New clients
    new_clients_q = await session.execute(
        select(func.count(Client.id)).where(Client.created_at >= start.isoformat())
    )
    new_clients = new_clients_q.scalar() or 0

    return {
        "period": period,
        "start_date": start.isoformat(),
        "total_bookings": total,
        "completed": completed,
        "cancelled": cancelled,
        "no_show": no_show,
        "revenue": revenue,
        "average_check": revenue // completed if completed > 0 else 0,
        "new_clients": new_clients,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
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

    return {
        "date": day.isoformat(),
        "bookings_count": len(bookings),
        "bookings": [
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
            }
            for b in bookings
        ],
    }


@router.get("/all-bookings")
async def get_all_bookings(
    start: date | None = None,
    end: date | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Get all bookings with optional filters."""
    from sqlalchemy import select as sel

    stmt = sel(Booking).order_by(Booking.date.desc(), Booking.time_start.desc())

    if start:
        stmt = stmt.where(Booking.date >= start)
    if end:
        stmt = stmt.where(Booking.date <= end)
    if status:
        stmt = stmt.where(Booking.status == BookingStatus(status))

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
