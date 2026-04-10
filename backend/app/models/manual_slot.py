from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ManualSlot(Base):
    __tablename__ = "manual_slots"
    __table_args__ = (
        UniqueConstraint("service_id", "date", "time_start", name="uq_slot_service_date_time"),
        Index("ix_slot_date_service", "date", "service_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time_start: Mapped[time] = mapped_column(Time, nullable=False)
    time_end: Mapped[time] = mapped_column(Time, nullable=False)
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"), nullable=True)

    # Manual booking fields (for Instagram/personal bookings without system booking)
    is_manual_booking: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_client_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    manual_note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    service = relationship("Service", lazy="selectin")
    booking = relationship("Booking", lazy="selectin")

    @property
    def is_booked(self) -> bool:
        return self.booking_id is not None or self.is_manual_booking
