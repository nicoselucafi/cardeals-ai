"""Offer search service with caching."""

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models import Offer, Dealer, SearchLog
from schemas import OfferResponse, SearchParams
from services.cache import get_cache_key, get_cached, set_cached

logger = logging.getLogger(__name__)


async def search_offers(
    db: AsyncSession,
    params: SearchParams,
) -> tuple[list[OfferResponse], dict]:
    """
    Search for vehicle offers with filters and caching.

    Returns:
        Tuple of (list of offers, filters_applied dict)
    """
    # Build cache key
    cache_key = get_cache_key(
        make=params.make,
        model=params.model,
        max_monthly_payment=params.max_monthly_payment,
        offer_type=params.offer_type,
        max_down_payment=params.max_down_payment,
        min_term_months=params.min_term_months,
        max_term_months=params.max_term_months,
        limit=params.limit,
        sort_by=params.sort_by,
    )

    # Check cache first
    cached_result = get_cached(cache_key)
    if cached_result is not None:
        logger.info(f"Returning cached results for: {params.make or 'all makes'} {params.model or 'all models'}")
        return cached_result

    # Build database query
    query = (
        select(Offer)
        .options(joinedload(Offer.dealer))
        .where(Offer.active == True)
    )

    filters_applied = {}

    # Apply filters
    if params.make:
        query = query.where(Offer.make.ilike(f"%{params.make}%"))
        filters_applied["make"] = params.make

    if params.model:
        query = query.where(Offer.model.ilike(f"%{params.model}%"))
        filters_applied["model"] = params.model

    if params.offer_type:
        query = query.where(Offer.offer_type == params.offer_type)
        filters_applied["offer_type"] = params.offer_type

    if params.max_monthly_payment is not None:
        query = query.where(Offer.monthly_payment <= params.max_monthly_payment)
        filters_applied["max_monthly_payment"] = params.max_monthly_payment

    if params.max_down_payment is not None:
        query = query.where(Offer.down_payment <= params.max_down_payment)
        filters_applied["max_down_payment"] = params.max_down_payment

    if params.min_term_months is not None:
        query = query.where(Offer.term_months >= params.min_term_months)
        filters_applied["min_term_months"] = params.min_term_months

    if params.max_term_months is not None:
        query = query.where(Offer.term_months <= params.max_term_months)
        filters_applied["max_term_months"] = params.max_term_months

    # Apply sorting
    if params.sort_by == "monthly_payment":
        query = query.order_by(Offer.monthly_payment.asc().nullslast())
    elif params.sort_by == "confidence_score":
        query = query.order_by(Offer.confidence_score.desc())
    elif params.sort_by == "down_payment":
        query = query.order_by(Offer.down_payment.asc().nullslast())
    else:
        query = query.order_by(Offer.monthly_payment.asc().nullslast())

    # Apply limit
    query = query.limit(params.limit)

    # Execute query
    result = await db.execute(query)
    offers = result.scalars().unique().all()

    # Convert to response format
    offer_responses = [
        OfferResponse(
            id=offer.id,
            dealer_id=offer.dealer_id,
            dealer_name=offer.dealer.name if offer.dealer else "Unknown",
            dealer_city=offer.dealer.city if offer.dealer else None,
            year=offer.year,
            make=offer.make,
            model=offer.model,
            trim=offer.trim,
            offer_type=offer.offer_type,
            monthly_payment=offer.monthly_payment,
            down_payment=offer.down_payment,
            term_months=offer.term_months,
            annual_mileage=offer.annual_mileage,
            apr=offer.apr,
            msrp=offer.msrp,
            source_url=offer.source_url,
            image_url=offer.image_url,
            confidence_score=offer.confidence_score,
            updated_at=offer.updated_at,
        )
        for offer in offers
    ]

    # Cache the results
    cache_result = (offer_responses, filters_applied)
    set_cached(cache_key, cache_result)

    make_str = params.make or "all makes"
    model_str = params.model or "all models"
    logger.info(f"Search returned {len(offer_responses)} offers for: {make_str} {model_str}")
    return cache_result


async def log_search(
    db: AsyncSession,
    raw_query: str,
    parsed_params: Optional[dict],
    results_count: int,
    cached: bool = False,
    user_id=None,
) -> None:
    """Log a search query to the database."""
    search_log = SearchLog(
        raw_query=raw_query,
        parsed_params=parsed_params,
        results_count=results_count,
        cached=cached,
        user_id=user_id,
    )
    db.add(search_log)
    await db.commit()
