from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db
from models import Offer
from schemas import OfferDetailResponse, OfferType, SearchParams, SearchResponse, SortField
from services.offer_search import search_offers as search_offers_service

router = APIRouter(prefix="/api/offers", tags=["offers"])


@router.get("/search", response_model=SearchResponse)
async def search_offers(
    make: str | None = Query(None, description="Vehicle make (Toyota, Honda)"),
    model: str | None = Query(None, description="Vehicle model name"),
    max_monthly_payment: float | None = Query(None, ge=0, le=10000, description="Max monthly payment"),
    offer_type: OfferType = Query(OfferType.lease, description="'lease' or 'finance'"),
    max_down_payment: float | None = Query(None, ge=0, le=100000, description="Max down payment"),
    min_term_months: int | None = Query(None, ge=1, le=84, description="Min term months"),
    max_term_months: int | None = Query(None, ge=1, le=84, description="Max term months"),
    limit: int = Query(10, ge=1, le=50, description="Results limit"),
    sort_by: SortField = Query(SortField.monthly_payment, description="Sort field"),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    Search for vehicle offers with optional filters.
    Returns matching offers sorted by the specified field.
    Uses in-memory caching (1 hour TTL) for performance.
    """
    params = SearchParams(
        make=make,
        model=model,
        max_monthly_payment=max_monthly_payment,
        offer_type=offer_type,
        max_down_payment=max_down_payment,
        min_term_months=min_term_months,
        max_term_months=max_term_months,
        limit=limit,
        sort_by=sort_by,
    )

    offer_responses, filters_applied = await search_offers_service(db, params)

    return SearchResponse(
        offers=offer_responses,
        total=len(offer_responses),
        filters_applied=filters_applied,
    )


@router.get("/{offer_id}", response_model=OfferDetailResponse)
async def get_offer(
    offer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> OfferDetailResponse:
    """
    Get full details for a single offer by ID.
    """
    query = (
        select(Offer)
        .options(joinedload(Offer.dealer))
        .where(Offer.id == offer_id)
    )

    result = await db.execute(query)
    offer = result.scalars().first()

    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    from schemas import DealerResponse

    return OfferDetailResponse(
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
        selling_price=offer.selling_price,
        offer_start_date=offer.offer_start_date,
        offer_end_date=offer.offer_end_date,
        disclaimer=offer.disclaimer,
        source_url=offer.source_url,
        source_pdf_url=offer.source_pdf_url,
        screenshot_url=offer.screenshot_url,
        image_url=offer.image_url,
        confidence_score=offer.confidence_score,
        extraction_method=offer.extraction_method,
        raw_extracted_data=offer.raw_extracted_data,
        verified_by_human=offer.verified_by_human,
        created_at=offer.created_at,
        updated_at=offer.updated_at,
        dealer=DealerResponse(
            id=offer.dealer.id,
            name=offer.dealer.name,
            slug=offer.dealer.slug,
            city=offer.dealer.city,
            state=offer.dealer.state,
            website=offer.dealer.website,
            specials_url=offer.dealer.specials_url,
            phone=offer.dealer.phone,
        ) if offer.dealer else None,
    )
