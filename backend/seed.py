"""Seed script: Insert 5 LA Toyota dealers and sample offers."""

import asyncio
from decimal import Decimal

from sqlalchemy import select
from database import async_session_maker
from models import Dealer, Offer


# 5 Real Toyota dealers in LA from CLAUDE.md
DEALERS = [
    {
        "name": "Longo Toyota",
        "slug": "longo-toyota",
        "address": "3534 Peck Rd",
        "city": "El Monte",
        "state": "CA",
        "zip": "91731",
        "latitude": Decimal("34.0753"),
        "longitude": Decimal("-118.0295"),
        "website": "https://www.longotoyota.com",
        "specials_url": "https://www.longotoyota.com/new-vehicle-specials/",
        "phone": "(626) 444-6666",
        "platform": "Custom",
    },
    {
        "name": "Toyota of Downtown LA",
        "slug": "toyota-downtown-la",
        "address": "1901 S Figueroa St",
        "city": "Los Angeles",
        "state": "CA",
        "zip": "90007",
        "latitude": Decimal("34.0332"),
        "longitude": Decimal("-118.2668"),
        "website": "https://www.toyotaofdowntownla.com",
        "specials_url": "https://www.toyotaofdowntownla.com/new-vehicle-specials/",
        "phone": "(213) 748-8822",
        "platform": "DealerOn",
    },
    {
        "name": "Toyota Santa Monica",
        "slug": "toyota-santa-monica",
        "address": "1600 Santa Monica Blvd",
        "city": "Santa Monica",
        "state": "CA",
        "zip": "90404",
        "latitude": Decimal("34.0259"),
        "longitude": Decimal("-118.4813"),
        "website": "https://www.santamonicatoyota.com",
        "specials_url": "https://www.santamonicatoyota.com/new-vehicle-specials/",
        "phone": "(310) 829-0808",
        "platform": "Dealer.com",
    },
    {
        "name": "Keyes Toyota",
        "slug": "keyes-toyota",
        "address": "5855 Van Nuys Blvd",
        "city": "Van Nuys",
        "state": "CA",
        "zip": "91401",
        "latitude": Decimal("34.1761"),
        "longitude": Decimal("-118.4490"),
        "website": "https://www.keystoyota.com",
        "specials_url": "https://www.keystoyota.com/new-vehicle-specials/",
        "phone": "(818) 904-2266",
        "platform": "DealerOn",
    },
    {
        "name": "Toyota of Glendora",
        "slug": "toyota-of-glendora",
        "address": "1001 S Lone Hill Ave",
        "city": "Glendora",
        "state": "CA",
        "zip": "91740",
        "latitude": Decimal("34.1156"),
        "longitude": Decimal("-117.8642"),
        "website": "https://www.toyotaofglendora.com",
        "specials_url": "https://www.toyotaofglendora.com/new-vehicle-specials/",
        "phone": "(909) 305-2000",
        "platform": "Dealer.com",
    },
]

# Sample offers (realistic prices from 2025)
# Format: (dealer_index, year, model, trim, monthly_payment, down_payment, term_months, mileage)
SAMPLE_OFFERS = [
    # Longo Toyota (index 0)
    (0, 2025, "RAV4", "LE", 299, 3499, 36, 12000),
    (0, 2025, "Camry", "LE", 279, 2999, 36, 12000),
    (0, 2025, "Corolla", "LE", 219, 2499, 36, 12000),

    # Toyota of Downtown LA (index 1)
    (1, 2025, "RAV4", "XLE", 329, 3999, 36, 12000),
    (1, 2025, "Highlander", "LE", 389, 3999, 36, 12000),
    (1, 2025, "Tacoma", "SR", 329, 3499, 36, 12000),

    # Toyota Santa Monica (index 2)
    (2, 2025, "RAV4", "LE", 309, 3299, 36, 12000),
    (2, 2025, "Camry", "SE", 299, 2999, 36, 12000),
    (2, 2025, "Prius", "LE", 269, 2999, 36, 12000),

    # Keyes Toyota (index 3)
    (3, 2025, "Corolla", "SE", 239, 2499, 36, 12000),
    (3, 2025, "RAV4", "LE", 289, 3499, 36, 12000),
    (3, 2025, "4Runner", "SR5", 449, 4499, 36, 12000),

    # Toyota of Glendora (index 4)
    (4, 2025, "Camry", "LE", 269, 2799, 36, 12000),
    (4, 2025, "Highlander", "XLE", 429, 4499, 36, 12000),
    (4, 2025, "Corolla Cross", "LE", 259, 2999, 36, 12000),
]


async def seed_database():
    """Insert dealers and sample offers into the database."""
    async with async_session_maker() as session:
        # Check if already seeded
        existing = await session.execute(select(Dealer).limit(1))
        if existing.scalars().first():
            print("Database already seeded. Skipping...")
            return

        print("Seeding database...")

        # Insert dealers
        dealer_objects = []
        for dealer_data in DEALERS:
            dealer = Dealer(**dealer_data, active=True, verified=False)
            session.add(dealer)
            dealer_objects.append(dealer)

        await session.flush()  # Get dealer IDs
        print(f"Inserted {len(dealer_objects)} dealers.")

        # Insert offers
        offer_count = 0
        for dealer_idx, year, model, trim, monthly, down, term, mileage in SAMPLE_OFFERS:
            dealer = dealer_objects[dealer_idx]
            offer = Offer(
                dealer_id=dealer.id,
                year=year,
                make="Toyota",
                model=model,
                trim=trim,
                offer_type="lease",
                monthly_payment=Decimal(str(monthly)),
                down_payment=Decimal(str(down)),
                term_months=term,
                annual_mileage=mileage,
                source_url=dealer.specials_url,
                confidence_score=Decimal("1.00"),  # Manual seed = verified
                extraction_method="manual_seed",
                active=True,
                verified_by_human=True,
            )
            session.add(offer)
            offer_count += 1

        await session.commit()
        print(f"Inserted {offer_count} offers.")
        print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
