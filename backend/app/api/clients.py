from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.client_service import ClientService

router = APIRouter(prefix="/api/clients", tags=["clients"])


class ClientResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    phone: str | None
    instagram_handle: str | None
    notes: str | None
    is_vip: bool
    visit_count: int
    total_spent: int
    referral_code: str | None

    model_config = {"from_attributes": True}


class ClientFromInstagram(BaseModel):
    instagram_handle: str
    name: str | None = None
    phone: str | None = None
    notes: str | None = None


class ClientUpdate(BaseModel):
    phone: str | None = None
    instagram_handle: str | None = None
    notes: str | None = None
    is_vip: bool | None = None


class ClientDetailResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    phone: str | None
    instagram_handle: str | None
    notes: str | None
    is_vip: bool
    visit_count: int
    total_spent: int
    referral_code: str | None
    created_at: str | None = None
    last_visit_at: str | None = None
    bookings: list = []
    average_check: int = 0


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    filter: str = "all",
    q: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    svc = ClientService(session)
    if q:
        clients = await svc.search(q)
    else:
        clients = await svc.get_all(filter)
    return clients


@router.get("/{client_id}", response_model=ClientDetailResponse)
async def get_client(client_id: int, session: AsyncSession = Depends(get_session)):
    from sqlalchemy import select
    from app.models.client import Client
    from app.services.booking_service import BookingService

    result = await session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    booking_svc = BookingService(session)
    bookings = await booking_svc.get_client_bookings(client_id)

    booking_list = [
        {
            "id": b.id,
            "service_name": b.service.name,
            "date": b.date.isoformat(),
            "time_start": b.time_start.strftime("%H:%M"),
            "time_end": b.time_end.strftime("%H:%M"),
            "status": b.status.value,
            "price": b.service.price,
        }
        for b in bookings
    ]

    return ClientDetailResponse(
        id=client.id,
        telegram_id=client.telegram_id,
        first_name=client.first_name,
        last_name=client.last_name,
        username=client.username,
        phone=client.phone,
        instagram_handle=client.instagram_handle,
        notes=client.notes,
        is_vip=client.is_vip,
        visit_count=client.visit_count,
        total_spent=client.total_spent,
        referral_code=client.referral_code,
        created_at=client.created_at.isoformat() if client.created_at else None,
        last_visit_at=client.last_visit_at.isoformat() if client.last_visit_at else None,
        bookings=booking_list,
        average_check=client.total_spent // client.visit_count if client.visit_count > 0 else 0,
    )


@router.get("/telegram/{telegram_id}", response_model=ClientResponse)
async def get_client_by_telegram(telegram_id: int, session: AsyncSession = Depends(get_session)):
    svc = ClientService(session)
    client = await svc.get_by_telegram_id(telegram_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("/from-instagram", response_model=ClientResponse)
async def create_from_instagram(
    data: ClientFromInstagram, session: AsyncSession = Depends(get_session)
):
    svc = ClientService(session)
    client = await svc.create_from_instagram(
        data.instagram_handle, data.name, data.phone, data.notes
    )
    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int, data: ClientUpdate, session: AsyncSession = Depends(get_session)
):
    from sqlalchemy import select
    from app.models.client import Client

    result = await session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(client, key, value)
    await session.commit()
    await session.refresh(client)
    return client
