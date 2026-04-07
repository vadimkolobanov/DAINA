"""Smoke test — verify test infra works."""
import pytest


@pytest.mark.asyncio
async def test_session_works(session):
    from sqlalchemy import text
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1
