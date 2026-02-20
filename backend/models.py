import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String, Text, Boolean, Integer, Date, DateTime,
    ForeignKey, Numeric, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Dealer(Base):
    """Toyota dealership information."""

    __tablename__ = "dealers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2), default="CA")
    zip: Mapped[Optional[str]] = mapped_column(String(10))
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    specials_url: Mapped[str] = mapped_column(String(500), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    platform: Mapped[Optional[str]] = mapped_column(String(100))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationship
    offers: Mapped[list["Offer"]] = relationship(
        "Offer",
        back_populates="dealer",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_dealers_active", "active", postgresql_where=(active == True)),
    )


class Offer(Base):
    """Vehicle lease/finance offer from a dealer."""

    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    dealer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dealers.id", ondelete="CASCADE"),
        nullable=False
    )

    # Vehicle info
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    make: Mapped[str] = mapped_column(String(50), default="Toyota", nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    trim: Mapped[Optional[str]] = mapped_column(String(100))

    # Offer details
    offer_type: Mapped[str] = mapped_column(String(20), default="lease", nullable=False)
    monthly_payment: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    down_payment: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    term_months: Mapped[Optional[int]] = mapped_column(Integer)
    annual_mileage: Mapped[Optional[int]] = mapped_column(Integer)
    apr: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    msrp: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    selling_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Offer validity
    offer_start_date: Mapped[Optional[date]] = mapped_column(Date)
    offer_end_date: Mapped[Optional[date]] = mapped_column(Date)
    disclaimer: Mapped[Optional[str]] = mapped_column(Text)

    # Source tracking (proof)
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    source_pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    screenshot_url: Mapped[Optional[str]] = mapped_column(String(500))
    image_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Quality tracking
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("0.80")
    )
    extraction_method: Mapped[Optional[str]] = mapped_column(String(50))
    raw_extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    verified_by_human: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationship
    dealer: Mapped["Dealer"] = relationship("Dealer", back_populates="offers")

    __table_args__ = (
        Index("idx_offers_active", "active", postgresql_where=(active == True)),
        Index("idx_offers_make_model", "make", "model", postgresql_where=(active == True)),
        Index("idx_offers_payment", "monthly_payment", postgresql_where=(active == True)),
        Index("idx_offers_dealer", "dealer_id", postgresql_where=(active == True)),
        Index("idx_offers_type", "offer_type", postgresql_where=(active == True)),
    )


class User(Base):
    """User account (minimal for V0)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class SearchLog(Base):
    """Log of user searches for analytics."""

    __tablename__ = "search_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    raw_query: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_params: Mapped[Optional[dict]] = mapped_column(JSONB)
    results_count: Mapped[Optional[int]] = mapped_column(Integer)
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        Index("idx_search_logs_created", "created_at"),
    )


class ChatUsage(Base):
    """Tracks per-user daily chat usage for free tier limits."""

    __tablename__ = "chat_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="chat")
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        Index("idx_chat_usage_user_date", "user_id", "used_at"),
    )
