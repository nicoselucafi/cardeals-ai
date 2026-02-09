from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

settings = get_settings()

# Create async engine
# Note: statement_cache_size=0 is required for pgbouncer/Supabase pooler
engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",  # Log SQL in dev
    pool_pre_ping=True,  # Check connection health
    connect_args={"statement_cache_size": 0},  # Required for pgbouncer
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
