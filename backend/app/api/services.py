from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import require_admin
from app.models.booking import Booking, BookingStatus
from app.models.service import Service

router = APIRouter(prefix="/api/services", tags=["services"])


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    duration_minutes: int
    price: int
    old_price: int | None = None
    photo_url: str | None
    is_active: bool
    sort_order: int = 0

    model_config = {"from_attributes": True}


class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    duration_minutes: int
    price: int
    old_price: int | None = None
    photo_url: str | None = None
    is_active: bool = True
    sort_order: int = 0


@router.get("", response_model=list[ServiceResponse])
async def list_services(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Service).where(Service.is_active == True).order_by(Service.sort_order)
    )
    return result.scalars().all()


@router.get("/all", response_model=list[ServiceResponse])
async def list_all_services(
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    """List all services including inactive (admin only)."""
    result = await session.execute(select(Service).order_by(Service.sort_order))
    return result.scalars().all()


def _validate_service(data: ServiceCreate):
    if not data.name or not data.name.strip():
        raise HTTPException(status_code=400, detail="Название услуги обязательно")
    if data.price < 0:
        raise HTTPException(status_code=400, detail="Цена не может быть отрицательной")
    if data.duration_minutes < 5:
        raise HTTPException(status_code=400, detail="Длительность не может быть меньше 5 минут")
    if data.old_price is not None and data.old_price <= data.price:
        raise HTTPException(status_code=400, detail="Цена до скидки должна быть выше текущей цены")


@router.post("", response_model=ServiceResponse)
async def create_service(
    data: ServiceCreate,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    _validate_service(data)
    service = Service(**data.model_dump())
    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    data: ServiceCreate,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    _validate_service(data)
    for key, value in data.model_dump().items():
        setattr(service, key, value)
    await session.commit()
    await session.refresh(service)
    return service


@router.delete("/{service_id}")
async def delete_service(
    service_id: int,
    admin_id: int = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    # Check for active bookings
    from sqlalchemy import func as sqlfunc
    active_count = await session.execute(
        select(sqlfunc.count(Booking.id)).where(
            Booking.service_id == service_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
    )
    if (active_count.scalar() or 0) > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить услугу с активными записями. Сначала отмените или завершите записи."
        )

    await session.delete(service)
    await session.commit()
    return {"ok": True}
