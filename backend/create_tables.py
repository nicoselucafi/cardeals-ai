"""Script to create all database tables."""

import asyncio
from database import engine, Base
from models import Dealer, Offer, User, SearchLog  # Import all models to register them


async def create_tables():
    """Create all tables in the database."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Done! Tables created successfully.")

    # Print created tables
    print("\nCreated tables:")
    for table in Base.metadata.tables:
        print(f"  - {table}")


if __name__ == "__main__":
    asyncio.run(create_tables())
