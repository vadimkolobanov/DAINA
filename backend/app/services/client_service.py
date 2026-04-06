from __future__ import annotations

import secrets

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client


class ClientService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str,
        last_name: str | None = None,
        username: str | None = None,
    ) -> tuple[Client, bool]:
        """Get existing client or create new one. Returns (client, is_new)."""
        result = await self.session.execute(
            select(Client).where(Client.telegram_id == telegram_id)
        )
        client = result.scalar_one_or_none()
        if client:
            # Update name if changed
            client.first_name = first_name
            if last_name:
                client.last_name = last_name
            if username:
                client.username = username
            await self.session.commit()
            return client, False

        client = Client(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            referral_code=secrets.token_urlsafe(8),
        )
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return client, True

    async def get_by_telegram_id(self, telegram_id: int) -> Client | None:
        result = await self.session.execute(
            select(Client).where(Client.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, code: str) -> Client | None:
        result = await self.session.execute(
            select(Client).where(Client.referral_code == code)
        )
        return result.scalar_one_or_none()

    async def link_instagram(self, client_id: int, instagram_handle: str) -> Client:
        result = await self.session.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one()
        client.instagram_handle = instagram_handle
        await self.session.commit()
        return client

    async def search(self, query: str) -> list[Client]:
        result = await self.session.execute(
            select(Client).where(
                or_(
                    Client.first_name.ilike(f"%{query}%"),
                    Client.last_name.ilike(f"%{query}%"),
                    Client.instagram_handle.ilike(f"%{query}%"),
                    Client.username.ilike(f"%{query}%"),
                )
            )
        )
        return list(result.scalars().all())

    async def get_all(self, filter_type: str = "all") -> list[Client]:
        stmt = select(Client)
        if filter_type == "vip":
            stmt = stmt.where(Client.is_vip == True)
        elif filter_type == "new":
            stmt = stmt.where(Client.visit_count == 0)
        stmt = stmt.order_by(Client.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_from_instagram(
        self, instagram_handle: str, name: str | None = None, phone: str | None = None, notes: str | None = None
    ) -> Client:
        """Create a placeholder client from Instagram (before they join Telegram)."""
        client = Client(
            telegram_id=None,  # will be updated when they join via deeplink
            first_name=name or instagram_handle,
            instagram_handle=instagram_handle,
            phone=phone,
            notes=notes,
            referral_code=secrets.token_urlsafe(8),
        )
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return client
