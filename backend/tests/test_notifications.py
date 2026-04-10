"""Tests for NotificationService — admin broadcast, null telegram_id."""
from __future__ import annotations

from datetime import date, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.booking import Booking, BookingStatus
from app.models.client import Client
from app.models.service import Service
from app.services.notification_service import NotificationService


def _make_booking(client: Client, service: Service) -> Booking:
    booking = MagicMock(spec=Booking)
    booking.id = 1
    booking.client = client
    booking.service = service
    booking.client_id = client.id if client.id else 1
    booking.service_id = service.id if service.id else 1
    booking.date = date(2026, 4, 10)
    booking.time_start = time(10, 0)
    booking.time_end = time(11, 0)
    booking.status = BookingStatus.PENDING
    return booking


def _make_client(telegram_id=111, first_name="Test"):
    client = MagicMock(spec=Client)
    client.id = 1
    client.telegram_id = telegram_id
    client.first_name = first_name
    client.last_name = None
    client.username = "testuser"
    client.phone = "+375291234567"
    client.instagram_handle = "test_insta"
    client.visit_count = 0
    return client


def _make_service():
    service = MagicMock(spec=Service)
    service.id = 1
    service.name = "Manicure"
    service.price = 30
    return service


@pytest.mark.asyncio
async def test_notify_client_skips_null_telegram_id(mock_bot):
    """Instagram clients with telegram_id=None should not crash."""
    client = _make_client(telegram_id=None)
    service = _make_service()
    booking = _make_booking(client, service)

    notifier = NotificationService(mock_bot, {"currency": "руб"})
    await notifier.notify_client_confirmed(booking)

    mock_bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_notify_client_sends_when_telegram_id_exists(mock_bot):
    client = _make_client(telegram_id=12345)
    service = _make_service()
    booking = _make_booking(client, service)

    notifier = NotificationService(mock_bot, {"currency": "руб"})
    await notifier.notify_client_confirmed(booking)

    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == 12345  # telegram_id


@pytest.mark.asyncio
async def test_notify_admin_sends_to_all_admin_ids(mock_bot):
    """Should send to all admins from config dict + bootstrap env admin."""
    client = _make_client()
    service = _make_service()
    booking = _make_booking(client, service)

    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.ADMIN_TELEGRAM_ID = 111
        mock_settings.WEBAPP_URL = "https://example.com"

        notifier = NotificationService(mock_bot, {"admin_ids": "111,222,333"})
        await notifier.notify_admin_new_booking(booking)

    # Should have been called for each admin (111 from env + 222, 333 from config)
    assert mock_bot.send_message.call_count == 3
    called_ids = {call[0][0] for call in mock_bot.send_message.call_args_list}
    assert called_ids == {111, 222, 333}


@pytest.mark.asyncio
async def test_completed_notification_includes_care_tips(mock_bot):
    client = _make_client(telegram_id=555)
    service = _make_service()
    booking = _make_booking(client, service)

    notifier = NotificationService(mock_bot, {"currency": "руб"})
    await notifier.notify_client_completed(booking, "Совет 1\nСовет 2")

    call_args = mock_bot.send_message.call_args
    text = call_args[1].get("text", call_args[0][1] if len(call_args[0]) > 1 else "")
    assert "Совет 1" in text
    assert "Совет 2" in text


@pytest.mark.asyncio
async def test_vip_notification(mock_bot):
    client = _make_client(telegram_id=777)

    notifier = NotificationService(mock_bot, {"vip_message": "Вы VIP!"})
    await notifier.notify_client_vip(client)

    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    text = call_args[1].get("text", call_args[0][1] if len(call_args[0]) > 1 else "")
    assert "VIP" in text


@pytest.mark.asyncio
async def test_noshow_notification_sends(mock_bot):
    client = _make_client(telegram_id=888)
    service = _make_service()
    booking = _make_booking(client, service)

    notifier = NotificationService(mock_bot, {})
    await notifier.notify_client_noshow(booking)

    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_cancelled_notification_sends(mock_bot):
    client = _make_client(telegram_id=999)
    service = _make_service()
    booking = _make_booking(client, service)

    notifier = NotificationService(mock_bot, {})
    await notifier.notify_client_cancelled(booking)

    mock_bot.send_message.assert_called_once()
