"""Tests for ClientService — create, link, search."""
from __future__ import annotations

import pytest
import pytest_asyncio

from app.models.client import Client
from app.services.client_service import ClientService


@pytest.mark.asyncio
async def test_get_or_create_new_client(session):
    svc = ClientService(session)
    client, is_new = await svc.get_or_create(
        telegram_id=100, first_name="Alice"
    )
    assert is_new is True
    assert client.id is not None
    assert client.first_name == "Alice"
    assert client.referral_code is not None


@pytest.mark.asyncio
async def test_get_or_create_existing_updates_name(session):
    svc = ClientService(session)
    client1, _ = await svc.get_or_create(telegram_id=200, first_name="Bob")
    client2, is_new = await svc.get_or_create(telegram_id=200, first_name="Bobby")
    assert is_new is False
    assert client2.id == client1.id
    assert client2.first_name == "Bobby"


@pytest.mark.asyncio
async def test_create_from_instagram_null_telegram_id(session):
    svc = ClientService(session)
    client = await svc.create_from_instagram("test_insta", name="Diana")
    assert client.telegram_id is None
    assert client.instagram_handle == "test_insta"
    assert client.first_name == "Diana"


@pytest.mark.asyncio
async def test_get_by_telegram_id(session):
    svc = ClientService(session)
    await svc.get_or_create(telegram_id=300, first_name="Charlie")
    found = await svc.get_by_telegram_id(300)
    assert found is not None
    assert found.first_name == "Charlie"


@pytest.mark.asyncio
async def test_get_by_telegram_id_not_found(session):
    svc = ClientService(session)
    found = await svc.get_by_telegram_id(999999)
    assert found is None


@pytest.mark.asyncio
async def test_get_by_referral_code(session):
    svc = ClientService(session)
    client, _ = await svc.get_or_create(telegram_id=400, first_name="Dave")
    found = await svc.get_by_referral_code(client.referral_code)
    assert found is not None
    assert found.id == client.id


@pytest.mark.asyncio
async def test_search_by_name(session):
    svc = ClientService(session)
    await svc.get_or_create(telegram_id=500, first_name="UniqueNameXYZ")
    results = await svc.search("UniqueNameXYZ")
    assert len(results) >= 1
    assert results[0].first_name == "UniqueNameXYZ"


@pytest.mark.asyncio
async def test_get_all_clients(session):
    svc = ClientService(session)
    await svc.get_or_create(telegram_id=600, first_name="Eve")
    all_clients = await svc.get_all()
    assert len(all_clients) >= 1


@pytest.mark.asyncio
async def test_get_all_vip_filter(session):
    svc = ClientService(session)
    client, _ = await svc.get_or_create(telegram_id=700, first_name="VipUser")
    client.is_vip = True
    await session.commit()

    vips = await svc.get_all(filter_type="vip")
    assert any(c.id == client.id for c in vips)
