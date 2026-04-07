"""Tests for BookingService — slots, creation, status, atomicity."""
from __future__ import annotations

from datetime import date, time, timedelta

import pytest
import pytest_asyncio

from app.models.booking import Booking, BookingStatus
from app.models.client import Client
from app.models.schedule import Schedule
from app.models.service import Service
from app.services.booking_service import BookingService


@pytest_asyncio.fixture
async def seed_data(session):
    """Create minimal data: 1 client, 1 service, Mon-Fri schedule."""
    client = Client(
        telegram_id=111,
        first_name="Test",
        referral_code="test123",
    )
    service = Service(
        name="Manicure",
        duration_minutes=60,
        price=30,
        sort_order=1,
    )
    # Monday schedule: 09:00 - 18:00
    sched = Schedule(
        day_of_week=0,
        is_working=True,
        time_start=time(9, 0),
        time_end=time(18, 0),
    )
    session.add_all([client, service, sched])
    await session.commit()
    await session.refresh(client)
    await session.refresh(service)
    return {"client": client, "service": service}


def _next_monday() -> date:
    today = date.today()
    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


# ── Available Slots ──


@pytest.mark.asyncio
async def test_available_slots_returns_slots(session, seed_data):
    svc = BookingService(session, slot_interval=60)
    monday = _next_monday()
    slots = await svc.get_available_slots(monday, 60)
    # 09:00..17:00 = 9 slots with 60min interval and 60min duration
    assert len(slots) == 9
    assert time(9, 0) in slots
    assert time(17, 0) in slots
    assert time(18, 0) not in slots


@pytest.mark.asyncio
async def test_available_slots_respects_interval(session, seed_data):
    svc = BookingService(session, slot_interval=30)
    monday = _next_monday()
    slots = await svc.get_available_slots(monday, 60)
    # 30min step, 60min duration: 09:00, 09:30, ..., 17:00 = 17 slots
    assert time(9, 0) in slots
    assert time(9, 30) in slots
    assert len(slots) == 17


@pytest.mark.asyncio
async def test_available_slots_excludes_booked(session, seed_data):
    data = seed_data
    monday = _next_monday()
    svc = BookingService(session, slot_interval=60)

    # Book 10:00 - 11:00
    await svc.create_booking(data["client"].id, data["service"].id, monday, time(10, 0), 60)

    slots = await svc.get_available_slots(monday, 60)
    assert time(10, 0) not in slots
    assert time(9, 0) in slots
    assert time(11, 0) in slots


@pytest.mark.asyncio
async def test_no_slots_on_non_working_day(session, seed_data):
    svc = BookingService(session, slot_interval=60)
    # Tuesday (weekday=1) — no schedule defined
    tuesday = _next_monday() + timedelta(days=1)
    slots = await svc.get_available_slots(tuesday, 60)
    assert slots == []


# ── Create Booking ──


@pytest.mark.asyncio
async def test_create_booking_success(session, seed_data):
    data = seed_data
    monday = _next_monday()
    svc = BookingService(session, slot_interval=60)

    booking = await svc.create_booking(
        data["client"].id, data["service"].id, monday, time(9, 0), 60
    )
    assert booking.id is not None
    assert booking.status == BookingStatus.PENDING
    assert booking.time_start == time(9, 0)
    assert booking.time_end == time(10, 0)


# ── Status Updates ──


@pytest.mark.asyncio
async def test_update_status_to_completed(session, seed_data):
    data = seed_data
    monday = _next_monday()
    svc = BookingService(session, slot_interval=60)

    booking = await svc.create_booking(
        data["client"].id, data["service"].id, monday, time(14, 0), 60
    )
    result = await svc.update_status(booking.id, BookingStatus.COMPLETED)
    assert result.status == BookingStatus.COMPLETED


@pytest.mark.asyncio
async def test_update_status_completed_increments_visit_count(session, seed_data):
    data = seed_data
    monday = _next_monday()
    svc = BookingService(session, slot_interval=60)

    booking = await svc.create_booking(
        data["client"].id, data["service"].id, monday, time(15, 0), 60
    )

    client_id = data["client"].id
    service_price = data["service"].price

    # Check initial
    from sqlalchemy import select
    client_before = (await session.execute(
        select(Client).where(Client.id == client_id)
    )).scalar_one()
    initial_count = client_before.visit_count

    await svc.update_status(booking.id, BookingStatus.COMPLETED)

    # Refresh from DB
    session.expire_all()
    client_after = (await session.execute(
        select(Client).where(Client.id == client_id)
    )).scalar_one()
    assert client_after.visit_count == initial_count + 1
    assert client_after.total_spent >= service_price


@pytest.mark.asyncio
async def test_update_status_nonexistent_returns_none(session, seed_data):
    svc = BookingService(session)
    result = await svc.update_status(99999, BookingStatus.COMPLETED)
    assert result is None


# ── Available Dates ──


@pytest.mark.asyncio
async def test_available_dates_range(session, seed_data):
    monday = _next_monday()
    svc = BookingService(session, slot_interval=60)
    dates = await svc.get_available_dates(monday, monday + timedelta(days=6), 60)
    assert len(dates) == 7
    # Monday should be available, other days no schedule
    monday_entry = next(d for d in dates if d["date"] == monday.isoformat())
    assert monday_entry["available"] is True


# ── Client Bookings ──


@pytest.mark.asyncio
async def test_get_client_bookings(session, seed_data):
    data = seed_data
    monday = _next_monday()
    svc = BookingService(session, slot_interval=60)

    await svc.create_booking(data["client"].id, data["service"].id, monday, time(11, 0), 60)
    await svc.create_booking(data["client"].id, data["service"].id, monday, time(13, 0), 60)

    bookings = await svc.get_client_bookings(data["client"].id)
    assert len(bookings) >= 2
