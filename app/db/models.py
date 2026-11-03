"""Database models. Only what alerts need; no user accounts."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    bin: Mapped[str] = mapped_column(String(10), index=True)
    channel: Mapped[str] = mapped_column(String(10))  # "email" | "sms"
    contact: Mapped[str] = mapped_column(String(255))  # deleted on unsubscribe
    lang: Mapped[str] = mapped_column(String(2), default="en")
    unsubscribe_token: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ViolationSnapshot(Base):
    __tablename__ = "violation_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    bin: Mapped[str] = mapped_column(String(10), index=True)
    violation_id: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20))
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
