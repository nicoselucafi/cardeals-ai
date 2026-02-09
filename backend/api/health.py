from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Dealer, Offer
from schemas import HealthResponse
from services.cache import get_cache_stats

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.
    Returns service status, offer count, dealer count, and last scrape time.
    """
    # Count active dealers
    dealers_result = await db.execute(
        select(func.count()).select_from(Dealer).where(Dealer.active == True)
    )
    dealers_count = dealers_result.scalar() or 0

    # Count active offers
    offers_result = await db.execute(
        select(func.count()).select_from(Offer).where(Offer.active == True)
    )
    offers_count = offers_result.scalar() or 0

    # Get last scrape time (most recent offer update)
    last_scrape_result = await db.execute(
        select(func.max(Offer.updated_at)).where(Offer.active == True)
    )
    last_scrape = last_scrape_result.scalar()

    return HealthResponse(
        status="ok",
        offers_count=offers_count,
        dealers_count=dealers_count,
        last_scrape=last_scrape,
    )


@router.get("/cache-stats")
async def cache_stats():
    """
    Get cache statistics for monitoring.
    Returns hits, misses, hit rate, and cache size.
    """
    return get_cache_stats()
