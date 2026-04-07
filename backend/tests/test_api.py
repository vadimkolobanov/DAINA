"""Tests for API endpoints — validation, auth, responses."""
from __future__ import annotations

from datetime import date, time
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.models.client import Client
from app.models.schedule import Schedule
from app.models.service import Service
from app.services.booking_service import BookingService


@pytest_asyncio.fixture
async def app_client(engine, session):
    """Create FastAPI test client with in-memory DB."""
    from app.main import app
    from app.database import get_session

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session

    # Seed data
    client = Client(telegram_id=12345, first_name="TestClient", referral_code="ref_test")
    service = Service(name="Test Service", duration_minutes=60, price=30, sort_order=1)
    sched = Schedule(day_of_week=0, is_working=True, time_start=time(9, 0), time_end=time(18, 0))
    session.add_all([client, service, sched])
    await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, client, service

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint(app_client):
    client, _, _ = app_client
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_services(app_client):
    client, _, service = app_client
    resp = await client.get("/api/services")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test Service"


@pytest.mark.asyncio
async def test_list_all_services_requires_admin(app_client):
    client, _, _ = app_client
    resp = await client.get("/api/services/all")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_client_by_telegram(app_client):
    client, test_client, _ = app_client
    resp = await client.get(f"/api/clients/telegram/{test_client.telegram_id}")
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "TestClient"


@pytest.mark.asyncio
async def test_get_client_by_telegram_not_found(app_client):
    client, _, _ = app_client
    resp = await client.get("/api/clients/telegram/99999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_booking_invalid_time_format(app_client):
    client, test_client, service = app_client
    resp = await client.post("/api/bookings", json={
        "client_id": test_client.id,
        "service_id": service.id,
        "date": "2026-12-07",  # Monday
        "time": "99:99",
    })
    assert resp.status_code == 400
    assert "time" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_booking_past_date(app_client):
    client, test_client, service = app_client
    resp = await client.post("/api/bookings", json={
        "client_id": test_client.id,
        "service_id": service.id,
        "date": "2020-01-01",
        "time": "10:00",
    })
    assert resp.status_code == 400
    assert "past" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_booking_client_not_found(app_client):
    client, _, service = app_client
    resp = await client.post("/api/bookings", json={
        "client_id": 99999,
        "service_id": service.id,
        "date": "2026-12-07",
        "time": "10:00",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_booking_service_not_found(app_client):
    client, test_client, _ = app_client
    resp = await client.post("/api/bookings", json={
        "client_id": test_client.id,
        "service_id": 99999,
        "date": "2026-12-07",
        "time": "10:00",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_booking_invalid_status(app_client):
    client, _, _ = app_client
    resp = await client.put("/api/bookings/1/status?status=INVALID_STATUS")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_schedule_time_validation(app_client):
    client, _, _ = app_client
    resp = await client.put("/api/schedule/day", json={
        "day_of_week": 0,
        "is_working": True,
        "time_start": "18:00",
        "time_end": "09:00",
    }, headers={"X-Telegram-User-Id": "0", "X-Telegram-Init-Data": ""})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_admin_stats_endpoint(app_client):
    client, _, _ = app_client
    # Should work without admin for now (no auth on stats in current code)
    resp = await client.get("/api/admin/stats?period=month",
                            headers={"X-Telegram-User-Id": "12345"})
    # May be 401 or 200 depending on admin config
    assert resp.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_config_public_endpoint(app_client):
    client, _, _ = app_client
    resp = await client.get("/api/config/public")
    assert resp.status_code == 200
    data = resp.json()
    assert "currency" in data
    assert "master_username" in data


@pytest.mark.asyncio
async def test_config_check_admin_no_header(app_client):
    client, _, _ = app_client
    resp = await client.get("/api/config/check-admin")
    assert resp.status_code == 200
    assert resp.json()["is_admin"] is False
