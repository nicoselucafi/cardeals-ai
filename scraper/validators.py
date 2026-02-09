"""Validate and clean extracted offer data."""

import logging
from datetime import datetime
from typing import Optional

from config import ALL_MODELS

logger = logging.getLogger(__name__)

# Valid term lengths
VALID_TERMS = [24, 27, 30, 33, 36, 39, 42, 48, 60, 72]

# Current and next year
CURRENT_YEAR = datetime.now().year
VALID_YEARS = [CURRENT_YEAR, CURRENT_YEAR + 1, CURRENT_YEAR - 1]

# Valid makes
VALID_MAKES = ["Toyota", "Honda", "Tesla"]


def normalize_model_name(model: str) -> Optional[str]:
    """
    Normalize model name to match our known models (Toyota, Honda, Tesla).
    Returns normalized name or None if not recognized.
    """
    if not model:
        return None

    model_lower = model.lower().strip()

    for known_model in ALL_MODELS:
        if known_model.lower() == model_lower:
            return known_model
        # Handle common variations
        if model_lower in known_model.lower() or known_model.lower() in model_lower:
            return known_model

    # Handle specific variations
    variations = {
        # Toyota
        "rav 4": "RAV4",
        "rav-4": "RAV4",
        "4 runner": "4Runner",
        "4-runner": "4Runner",
        "gr 86": "GR86",
        "gr-86": "GR86",
        "gr supra": "GR Supra",
        "gr-supra": "GR Supra",
        "corolla cross": "Corolla Cross",
        "grand highlander": "Grand Highlander",
        "land cruiser": "Land Cruiser",
        # Honda
        "cr-v": "CR-V",
        "crv": "CR-V",
        "hr-v": "HR-V",
        "hrv": "HR-V",
        # Tesla
        "model3": "Model 3",
        "modely": "Model Y",
        "models": "Model S",
        "modelx": "Model X",
    }

    for variation, normalized in variations.items():
        if variation in model_lower:
            return normalized

    logger.warning(f"Unknown model: {model}")
    return None


def normalize_make(make: str) -> str:
    """Normalize make name."""
    if not make:
        return "Toyota"  # Default
    make_lower = make.lower().strip()
    for valid_make in VALID_MAKES:
        if valid_make.lower() == make_lower:
            return valid_make
    return make.title()  # Capitalize if unknown


def validate_offer(offer: dict) -> tuple[bool, list[str]]:
    """
    Validate an extracted offer.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Required fields
    if not offer.get("model"):
        errors.append("Missing model")

    if not offer.get("year"):
        errors.append("Missing year")

    # Validate monthly payment
    monthly = offer.get("monthly_payment")
    if monthly is not None:
        try:
            monthly = float(monthly)
            if monthly < 50 or monthly > 2000:
                errors.append(f"monthly_payment out of range: {monthly}")
        except (TypeError, ValueError):
            errors.append(f"Invalid monthly_payment: {monthly}")

    # Validate down payment
    down = offer.get("down_payment")
    if down is not None:
        try:
            down = float(down)
            if down < 0 or down > 20000:
                errors.append(f"down_payment out of range: {down}")
        except (TypeError, ValueError):
            errors.append(f"Invalid down_payment: {down}")

    # Validate term
    term = offer.get("term_months")
    if term is not None:
        try:
            term = int(term)
            if term not in VALID_TERMS:
                # Allow close matches
                closest = min(VALID_TERMS, key=lambda x: abs(x - term))
                if abs(closest - term) <= 3:
                    logger.debug(f"Adjusted term {term} to {closest}")
                else:
                    errors.append(f"Invalid term_months: {term}")
        except (TypeError, ValueError):
            errors.append(f"Invalid term_months: {term}")

    # Validate year
    year = offer.get("year")
    if year is not None:
        try:
            year = int(year)
            if year not in VALID_YEARS:
                errors.append(f"Invalid year: {year}")
        except (TypeError, ValueError):
            errors.append(f"Invalid year: {year}")

    # Validate model name
    model = offer.get("model")
    if model:
        normalized = normalize_model_name(model)
        if normalized is None:
            errors.append(f"Unknown model: {model}")

    # Validate confidence
    confidence = offer.get("confidence", 0.8)
    try:
        confidence = float(confidence)
        if confidence < 0.5:
            errors.append(f"Confidence too low: {confidence}")
    except (TypeError, ValueError):
        pass  # Use default

    # Validate offer type
    offer_type = offer.get("offer_type", "lease")
    if offer_type not in ["lease", "finance"]:
        errors.append(f"Invalid offer_type: {offer_type}")

    is_valid = len(errors) == 0
    return is_valid, errors


def clean_offer(offer: dict) -> dict:
    """
    Clean and normalize offer data.
    Converts strings to proper types, normalizes model names, etc.
    """
    cleaned = {}

    # Year
    try:
        cleaned["year"] = int(offer.get("year", CURRENT_YEAR))
    except (TypeError, ValueError):
        cleaned["year"] = CURRENT_YEAR

    # Make (Toyota, Honda, Tesla, etc.)
    cleaned["make"] = normalize_make(offer.get("make", "Toyota"))

    # Image URL (pass through if present)
    cleaned["image_url"] = offer.get("image_url")

    # Model (normalized)
    model = offer.get("model", "")
    cleaned["model"] = normalize_model_name(model) or model

    # Trim
    cleaned["trim"] = offer.get("trim") or None

    # Offer type
    offer_type = offer.get("offer_type", "lease").lower()
    cleaned["offer_type"] = offer_type if offer_type in ["lease", "finance"] else "lease"

    # Monthly payment
    try:
        cleaned["monthly_payment"] = float(offer["monthly_payment"]) if offer.get("monthly_payment") else None
    except (TypeError, ValueError):
        cleaned["monthly_payment"] = None

    # Down payment
    try:
        cleaned["down_payment"] = float(offer["down_payment"]) if offer.get("down_payment") else None
    except (TypeError, ValueError):
        cleaned["down_payment"] = None

    # Term months
    try:
        term = int(offer["term_months"]) if offer.get("term_months") else None
        if term and term not in VALID_TERMS:
            # Snap to closest valid term
            term = min(VALID_TERMS, key=lambda x: abs(x - term))
        cleaned["term_months"] = term
    except (TypeError, ValueError):
        cleaned["term_months"] = None

    # Annual mileage
    try:
        cleaned["annual_mileage"] = int(offer["annual_mileage"]) if offer.get("annual_mileage") else None
    except (TypeError, ValueError):
        cleaned["annual_mileage"] = None

    # APR
    try:
        cleaned["apr"] = float(offer["apr"]) if offer.get("apr") else None
    except (TypeError, ValueError):
        cleaned["apr"] = None

    # MSRP
    try:
        cleaned["msrp"] = float(offer["msrp"]) if offer.get("msrp") else None
    except (TypeError, ValueError):
        cleaned["msrp"] = None

    # Selling price
    try:
        cleaned["selling_price"] = float(offer["selling_price"]) if offer.get("selling_price") else None
    except (TypeError, ValueError):
        cleaned["selling_price"] = None

    # Offer end date
    cleaned["offer_end_date"] = offer.get("offer_end_date") or None

    # Disclaimer
    cleaned["disclaimer"] = offer.get("disclaimer") or None

    # Confidence
    try:
        cleaned["confidence"] = float(offer.get("confidence", 0.8))
    except (TypeError, ValueError):
        cleaned["confidence"] = 0.8

    return cleaned


if __name__ == "__main__":
    # Test validation
    test_offer = {
        "year": 2025,
        "model": "rav4",
        "trim": "LE",
        "offer_type": "lease",
        "monthly_payment": 299,
        "down_payment": 3499,
        "term_months": 36,
        "annual_mileage": 12000,
        "confidence": 0.9,
    }

    is_valid, errors = validate_offer(test_offer)
    print(f"Valid: {is_valid}, Errors: {errors}")

    cleaned = clean_offer(test_offer)
    print(f"Cleaned: {cleaned}")
