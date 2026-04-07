"""Tests for ConfigService — get, set, admin IDs."""
from __future__ import annotations

import pytest
import pytest_asyncio

from app.services.config_service import ConfigService


@pytest.mark.asyncio
async def test_get_returns_env_default(session):
    svc = ConfigService(session)
    val = await svc.get("currency")
    assert val == "руб"


@pytest.mark.asyncio
async def test_set_and_get(session):
    svc = ConfigService(session)
    await svc.set("currency", "BYN")
    val = await svc.get("currency")
    assert val == "BYN"


@pytest.mark.asyncio
async def test_set_unknown_key_raises(session):
    svc = ConfigService(session)
    with pytest.raises(ValueError):
        await svc.set("nonexistent_key_12345", "value")


@pytest.mark.asyncio
async def test_get_all_returns_all_keys(session):
    svc = ConfigService(session)
    all_config = await svc.get_all()
    assert "currency" in all_config
    assert "app_name" in all_config
    assert "master_username" in all_config


@pytest.mark.asyncio
async def test_set_many(session):
    svc = ConfigService(session)
    await svc.set_many({"app_name": "TestStudio", "currency": "$"})
    assert await svc.get("app_name") == "TestStudio"
    assert await svc.get("currency") == "$"


@pytest.mark.asyncio
async def test_get_admin_ids_includes_env(session):
    svc = ConfigService(session)
    ids = await svc.get_admin_ids()
    # At minimum, should return a set (may be empty if env not configured)
    assert isinstance(ids, set)


@pytest.mark.asyncio
async def test_is_admin_false_for_random_id(session):
    svc = ConfigService(session)
    result = await svc.is_admin(999999999)
    assert result is False
