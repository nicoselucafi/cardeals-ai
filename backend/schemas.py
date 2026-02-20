from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from enum import Enum

from pydantic import BaseModel, Field


# ----- Dealer Schemas -----

class DealerResponse(BaseModel):
    """Dealer information for API responses."""
    id: UUID
    name: str
    slug: str
    city: Optional[str] = None
    state: str = "CA"
    website: Optional[str] = None
    specials_url: str
    phone: Optional[str] = None

    model_config = {"from_attributes": True}


# ----- Offer Schemas -----

class OfferResponse(BaseModel):
    """Offer summary for search results."""
    id: UUID
    dealer_id: UUID
    dealer_name: str  # Joined from dealer
    dealer_city: Optional[str] = None  # Joined from dealer

    # Vehicle info
    year: int
    make: str = "Toyota"
    model: str
    trim: Optional[str] = None

    # Offer details
    offer_type: str = "lease"
    monthly_payment: Optional[Decimal] = None
    down_payment: Optional[Decimal] = None
    term_months: Optional[int] = None
    annual_mileage: Optional[int] = None
    apr: Optional[Decimal] = None
    msrp: Optional[Decimal] = None

    # Source & quality
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    confidence_score: Decimal = Decimal("0.80")
    updated_at: datetime

    model_config = {"from_attributes": True}


class OfferDetailResponse(OfferResponse):
    """Full offer detail including all fields."""
    apr: Optional[Decimal] = None
    msrp: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    offer_start_date: Optional[date] = None
    offer_end_date: Optional[date] = None
    disclaimer: Optional[str] = None
    source_pdf_url: Optional[str] = None
    screenshot_url: Optional[str] = None
    extraction_method: Optional[str] = None
    raw_extracted_data: Optional[dict] = None
    verified_by_human: bool = False
    created_at: datetime

    # Full dealer info
    dealer: Optional[DealerResponse] = None


# ----- Search Schemas -----

class OfferType(str, Enum):
    lease = "lease"
    finance = "finance"


class SortField(str, Enum):
    monthly_payment = "monthly_payment"
    confidence_score = "confidence_score"
    down_payment = "down_payment"


class SearchParams(BaseModel):
    """Query parameters for offer search."""
    make: Optional[str] = Field(None, description="Vehicle make (e.g., 'Toyota', 'Honda')")
    model: Optional[str] = Field(None, description="Vehicle model name (e.g., 'RAV4', 'Camry', 'Civic')")
    max_monthly_payment: Optional[float] = Field(None, ge=0, le=10000, description="Maximum monthly payment in dollars")
    offer_type: Optional[OfferType] = Field(OfferType.lease, description="'lease' or 'finance'")
    max_down_payment: Optional[float] = Field(None, ge=0, le=100000, description="Maximum down payment in dollars")
    min_term_months: Optional[int] = Field(None, ge=1, le=84, description="Minimum term in months")
    max_term_months: Optional[int] = Field(None, ge=1, le=84, description="Maximum term in months")
    limit: int = Field(10, ge=1, le=50, description="Number of results to return")
    sort_by: SortField = Field(SortField.monthly_payment, description="Sort field")


class SearchResponse(BaseModel):
    """Response for offer search endpoint."""
    offers: list[OfferResponse]
    total: int
    filters_applied: dict


# ----- Chat Schemas -----

class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=5000, description="User's search query or comparison prompt")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    offers: list[OfferResponse]
    search_params: Optional[dict] = None
    remaining_prompts: Optional[int] = None
    daily_limit: Optional[int] = None
    is_premium: bool = False


class ChatUsageResponse(BaseModel):
    """Response for chat usage check endpoint."""
    used: int
    limit: int
    remaining: int
    is_premium: bool = False


# ----- Health Schemas -----

class HealthResponse(BaseModel):
    """Response for health check endpoint."""
    status: str
    offers_count: int
    dealers_count: int
    last_scrape: Optional[datetime] = None
