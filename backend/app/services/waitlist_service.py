from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.waitlist import WaitlistEntry, WaitlistStatus

logger = logging.getLogger(__name__)

OFFER_TIMEOUT_MINUTES = 30


class WaitlistService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_to_waitlist(self, client_id: int, service_id: int) -> WaitlistEntry:
        # Check if already waiting
        existing = await self.session.execute(
            select(WaitlistEntry).where(
                and_(
                    WaitlistEntry.client_id == client_id,
                    WaitlistEntry.service_id == service_id,
                    WaitlistEntry.status.in_([WaitlistStatus.WAITING, WaitlistStatus.NOTIFIED]),
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Already in waitlist")

        entry = WaitlistEntry(
            client_id=client_id,
            service_id=service_id,
            status=WaitlistStatus.WAITING,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def remove_from_waitlist(self, client_id: int, service_id: int) -> bool:
        result = await self.session.execute(
            select(WaitlistEntry).where(
                and_(
                    WaitlistEntry.client_id == client_id,
                    WaitlistEntry.service_id == service_id,
                    WaitlistEntry.status.in_([WaitlistStatus.WAITING, WaitlistStatus.NOTIFIED]),
                )
            )
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return False
        entry.status = WaitlistStatus.CANCELLED
        await self.session.commit()
        return True

    async def get_waitlist_position(self, client_id: int, service_id: int) -> int | None:
        """Return 1-based position or None if not in waitlist."""
        result = await self.session.execute(
            select(WaitlistEntry).where(
                and_(
                    WaitlistEntry.service_id == service_id,
                    WaitlistEntry.status == WaitlistStatus.WAITING,
                )
            ).order_by(WaitlistEntry.created_at)
        )
        entries = result.scalars().all()
        for i, entry in enumerate(entries):
            if entry.client_id == client_id:
                return i + 1
        return None

    async def is_in_waitlist(self, client_id: int, service_id: int) -> bool:
        result = await self.session.execute(
            select(WaitlistEntry).where(
                and_(
                    WaitlistEntry.client_id == client_id,
                    WaitlistEntry.service_id == service_id,
                    WaitlistEntry.status.in_([WaitlistStatus.WAITING, WaitlistStatus.NOTIFIED]),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_service_waitlist(self, service_id: int) -> list[WaitlistEntry]:
        result = await self.session.execute(
            select(WaitlistEntry).where(
                and_(
                    WaitlistEntry.service_id == service_id,
                    WaitlistEntry.status.in_([WaitlistStatus.WAITING, WaitlistStatus.NOTIFIED]),
                )
            ).order_by(WaitlistEntry.created_at)
        )
        return list(result.scalars().all())

    async def get_next_waiting(self, service_id: int) -> WaitlistEntry | None:
        """Get the first person in line (status=WAITING)."""
        result = await self.session.execute(
            select(WaitlistEntry).where(
                and_(
                    WaitlistEntry.service_id == service_id,
                    WaitlistEntry.status == WaitlistStatus.WAITING,
                )
            ).order_by(WaitlistEntry.created_at).limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_notified(self, entry_id: int) -> WaitlistEntry | None:
        result = await self.session.execute(
            select(WaitlistEntry).where(WaitlistEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None
        entry.status = WaitlistStatus.NOTIFIED
        entry.notified_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def accept_offer(self, entry_id: int) -> WaitlistEntry | None:
        result = await self.session.execute(
            select(WaitlistEntry).where(
                and_(
                    WaitlistEntry.id == entry_id,
                    WaitlistEntry.status == WaitlistStatus.NOTIFIED,
                )
            )
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None
        entry.status = WaitlistStatus.BOOKED
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def decline_offer(self, entry_id: int) -> WaitlistEntry | None:
        result = await self.session.execute(
            select(WaitlistEntry).where(
                and_(
                    WaitlistEntry.id == entry_id,
                    WaitlistEntry.status == WaitlistStatus.NOTIFIED,
                )
            )
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None
        entry.status = WaitlistStatus.CANCELLED
        await self.session.commit()
        return entry

    async def expire_stale_offers(self) -> list[int]:
        """Expire offers older than OFFER_TIMEOUT_MINUTES. Returns service_ids needing notify_next."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=OFFER_TIMEOUT_MINUTES)
        result = await self.session.execute(
            select(WaitlistEntry).where(
                and_(
                    WaitlistEntry.status == WaitlistStatus.NOTIFIED,
                    WaitlistEntry.notified_at < cutoff,
                )
            )
        )
        entries = result.scalars().all()
        service_ids = set()
        for entry in entries:
            entry.status = WaitlistStatus.EXPIRED
            service_ids.add(entry.service_id)
        if entries:
            await self.session.commit()
        return list(service_ids)

    async def get_waiting_count(self, service_id: int) -> int:
        result = await self.session.execute(
            select(func.count(WaitlistEntry.id)).where(
                and_(
                    WaitlistEntry.service_id == service_id,
                    WaitlistEntry.status == WaitlistStatus.WAITING,
                )
            )
        )
        return result.scalar() or 0
