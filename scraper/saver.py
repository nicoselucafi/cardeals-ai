"""Save extracted offers to the database."""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session, sessionmaker

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Create sync engine for scraper (not async like backend)
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


# We need to import the models - but they're in the backend folder
# For the scraper, we'll define minimal models here to avoid import issues

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Date, DateTime,
    ForeignKey, Numeric, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Dealer(Base):
    """Dealer model for scraper."""
    __tablename__ = "dealers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(2), default="CA")
    zip = Column(String(10))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    website = Column(String(500))
    specials_url = Column(String(500), nullable=False)
    phone = Column(String(20))
    platform = Column(String(100))
    verified = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class Offer(Base):
    """Offer model for scraper."""
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dealer_id = Column(UUID(as_uuid=True), ForeignKey("dealers.id"), nullable=False)

    year = Column(Integer, nullable=False)
    make = Column(String(50), default="Toyota", nullable=False)
    model = Column(String(100), nullable=False)
    trim = Column(String(100))

    offer_type = Column(String(20), default="lease", nullable=False)
    monthly_payment = Column(Numeric(10, 2))
    down_payment = Column(Numeric(10, 2))
    term_months = Column(Integer)
    annual_mileage = Column(Integer)
    apr = Column(Numeric(5, 2))
    msrp = Column(Numeric(10, 2))
    selling_price = Column(Numeric(10, 2))

    offer_start_date = Column(Date)
    offer_end_date = Column(Date)
    disclaimer = Column(Text)

    source_url = Column(String(500))
    source_pdf_url = Column(String(500))
    screenshot_url = Column(String(500))
    image_url = Column(String(500))

    confidence_score = Column(Numeric(3, 2), default=Decimal("0.80"))
    extraction_method = Column(String(50))
    raw_extracted_data = Column(JSONB)

    active = Column(Boolean, default=True)
    verified_by_human = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


def get_dealer_by_slug(session: Session, slug: str) -> Optional[Dealer]:
    """Get dealer by slug."""
    result = session.execute(
        select(Dealer).where(Dealer.slug == slug, Dealer.active == True)
    )
    return result.scalars().first()


def get_or_create_dealer(session: Session, dealer_info: dict) -> Dealer:
    """
    Get existing dealer or create a new one.

    Args:
        session: Database session
        dealer_info: Dict with name, slug, city, specials_url

    Returns:
        Dealer instance
    """
    dealer = get_dealer_by_slug(session, dealer_info["slug"])
    if dealer:
        return dealer

    # Create new dealer
    logger.info(f"Creating new dealer: {dealer_info['name']}")
    dealer = Dealer(
        name=dealer_info["name"],
        slug=dealer_info["slug"],
        city=dealer_info.get("city"),
        state="CA",
        specials_url=dealer_info["specials_url"],
        active=True,
    )
    session.add(dealer)
    session.flush()  # Get the ID without committing
    return dealer


def deactivate_dealer_offers(session: Session, dealer_id: uuid.UUID) -> int:
    """
    Deactivate all active offers for a dealer.
    Returns count of deactivated offers.
    """
    result = session.execute(
        update(Offer)
        .where(Offer.dealer_id == dealer_id, Offer.active == True)
        .values(active=False)
    )
    return result.rowcount


def save_offers(dealer_info: dict, offers: list[dict], source_url: str) -> dict:
    """
    Save extracted offers to the database.

    Args:
        dealer_info: Dict with dealer name, slug, city, specials_url
        offers: List of cleaned offer dictionaries
        source_url: URL where offers were scraped from

    Returns:
        Dict with stats: {deactivated: int, inserted: int, errors: int}
    """
    stats = {"deactivated": 0, "inserted": 0, "errors": 0}

    with SessionLocal() as session:
        # Get or create dealer
        dealer = get_or_create_dealer(session, dealer_info)

        logger.info(f"Saving offers for {dealer.name} (ID: {dealer.id})")

        # Deactivate old offers
        deactivated = deactivate_dealer_offers(session, dealer.id)
        stats["deactivated"] = deactivated
        logger.info(f"Deactivated {deactivated} old offers")

        # Insert new offers
        for offer_data in offers:
            try:
                # Append anchor fragment to source_url for deep linking
                offer_source_url = source_url
                anchor = offer_data.get("source_anchor")
                if anchor:
                    offer_source_url = f"{source_url}#{anchor}"

                offer = Offer(
                    dealer_id=dealer.id,
                    year=offer_data["year"],
                    make=offer_data.get("make", "Toyota"),
                    model=offer_data["model"],
                    trim=offer_data.get("trim"),
                    offer_type=offer_data.get("offer_type", "lease"),
                    monthly_payment=Decimal(str(offer_data["monthly_payment"])) if offer_data.get("monthly_payment") else None,
                    down_payment=Decimal(str(offer_data["down_payment"])) if offer_data.get("down_payment") else None,
                    term_months=offer_data.get("term_months"),
                    annual_mileage=offer_data.get("annual_mileage"),
                    apr=Decimal(str(offer_data["apr"])) if offer_data.get("apr") else None,
                    msrp=Decimal(str(offer_data["msrp"])) if offer_data.get("msrp") else None,
                    selling_price=Decimal(str(offer_data["selling_price"])) if offer_data.get("selling_price") else None,
                    disclaimer=offer_data.get("disclaimer"),
                    source_url=offer_source_url,
                    image_url=offer_data.get("image_url"),
                    confidence_score=Decimal(str(offer_data.get("confidence", 0.8))),
                    extraction_method=offer_data.get("extraction_method", "llm_html"),
                    raw_extracted_data=offer_data,
                    active=True,
                    verified_by_human=False,
                )
                session.add(offer)
                stats["inserted"] += 1

            except Exception as e:
                logger.error(f"Error saving offer: {e}")
                logger.debug(f"Offer data: {offer_data}")
                stats["errors"] += 1

        session.commit()
        logger.info(f"Inserted {stats['inserted']} new offers")

    return stats


if __name__ == "__main__":
    # Test database connection
    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        dealers = session.execute(select(Dealer).where(Dealer.active == True)).scalars().all()
        print(f"Found {len(dealers)} active dealers:")
        for d in dealers:
            print(f"  - {d.name} ({d.slug})")
