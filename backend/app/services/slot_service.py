from __future__ import annotations

from datetime import date, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manual_slot import ManualSlot


class SlotService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_slot(
        self, service_id: int, target_date: date, time_start: time, time_end: time
    ) -> ManualSlot:
        slot = ManualSlot(
            service_id=service_id,
            date=target_date,
            time_start=time_start,
            time_end=time_end,
        )
        self.session.add(slot)
        await self.session.commit()
        await self.session.refresh(slot)
        return slot

    async def create_slots_batch(
        self, slots: list[dict]
    ) -> list[ManualSlot]:
        created = []
        for s in slots:
            slot = ManualSlot(
                service_id=s["service_id"],
                date=s["date"],
                time_start=s["time_start"],
                time_end=s["time_end"],
            )
            self.session.add(slot)
            created.append(slot)
        await self.session.commit()
        for slot in created:
            await self.session.refresh(slot)
        return created

    async def delete_slot(self, slot_id: int) -> bool:
        result = await self.session.execute(
            select(ManualSlot).where(ManualSlot.id == slot_id)
        )
        slot = result.scalar_one_or_none()
        if not slot:
            return False
        if slot.is_booked:
            raise ValueError("Cannot delete a booked slot")
        await self.session.delete(slot)
        await self.session.commit()
        return True

    async def get_slots_by_date(self, target_date: date) -> list[ManualSlot]:
        result = await self.session.execute(
            select(ManualSlot)
            .where(ManualSlot.date == target_date)
            .order_by(ManualSlot.time_start)
        )
        return list(result.scalars().all())

    async def get_available_slots(
        self, target_date: date, service_id: int
    ) -> list[ManualSlot]:
        result = await self.session.execute(
            select(ManualSlot).where(
                and_(
                    ManualSlot.date == target_date,
                    ManualSlot.service_id == service_id,
                    ManualSlot.booking_id.is_(None),
                    ManualSlot.is_manual_booking == False,
                )
            ).order_by(ManualSlot.time_start)
        )
        return list(result.scalars().all())

    async def get_available_dates(
        self, service_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        result = await self.session.execute(
            select(ManualSlot.date, func.count(ManualSlot.id))
            .where(
                and_(
                    ManualSlot.service_id == service_id,
                    ManualSlot.date.between(start_date, end_date),
                    ManualSlot.booking_id.is_(None),
                    ManualSlot.is_manual_booking == False,
                )
            )
            .group_by(ManualSlot.date)
        )
        counts = {row[0]: row[1] for row in result.all()}

        dates = []
        from datetime import timedelta
        current = start_date
        while current <= end_date:
            cnt = counts.get(current, 0)
            dates.append({
                "date": current.isoformat(),
                "available": cnt > 0,
                "slots_count": cnt,
            })
            current += timedelta(days=1)
        return dates

    async def get_slot_dates_summary(
        self, start_date: date, end_date: date
    ) -> list[dict]:
        """Get summary of all slots per date (for admin calendar overview)."""
        result = await self.session.execute(
            select(
                ManualSlot.date,
                func.count(ManualSlot.id).label("total"),
                func.count(ManualSlot.id).filter(
                    and_(
                        ManualSlot.booking_id.is_(None),
                        ManualSlot.is_manual_booking == False,
                    )
                ).label("available"),
            )
            .where(ManualSlot.date.between(start_date, end_date))
            .group_by(ManualSlot.date)
        )
        return [
            {
                "date": row.date.isoformat(),
                "total": row.total,
                "available": row.available,
            }
            for row in result.all()
        ]

    async def book_slot(
        self, service_id: int, target_date: date, time_start: time, booking_id: int
    ) -> ManualSlot | None:
        result = await self.session.execute(
            select(ManualSlot).where(
                and_(
                    ManualSlot.service_id == service_id,
                    ManualSlot.date == target_date,
                    ManualSlot.time_start == time_start,
                    ManualSlot.booking_id.is_(None),
                    ManualSlot.is_manual_booking == False,
                )
            ).with_for_update()
        )
        slot = result.scalar_one_or_none()
        if not slot:
            return None
        slot.booking_id = booking_id
        await self.session.commit()
        await self.session.refresh(slot)
        return slot

    async def release_slot(self, booking_id: int) -> None:
        result = await self.session.execute(
            select(ManualSlot).where(ManualSlot.booking_id == booking_id)
        )
        slot = result.scalar_one_or_none()
        if slot:
            slot.booking_id = None
            await self.session.commit()

    async def manual_book_slot(
        self, slot_id: int, client_name: str, note: str | None = None
    ) -> ManualSlot | None:
        result = await self.session.execute(
            select(ManualSlot).where(ManualSlot.id == slot_id)
        )
        slot = result.scalar_one_or_none()
        if not slot or slot.is_booked:
            return None
        slot.is_manual_booking = True
        slot.manual_client_name = client_name
        slot.manual_note = note
        await self.session.commit()
        await self.session.refresh(slot)
        return slot

    async def manual_unbook_slot(self, slot_id: int) -> ManualSlot | None:
        result = await self.session.execute(
            select(ManualSlot).where(ManualSlot.id == slot_id)
        )
        slot = result.scalar_one_or_none()
        if not slot or not slot.is_manual_booking:
            return None
        slot.is_manual_booking = False
        slot.manual_client_name = None
        slot.manual_note = None
        await self.session.commit()
        await self.session.refresh(slot)
        return slot
