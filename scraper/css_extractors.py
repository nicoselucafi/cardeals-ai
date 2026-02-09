"""Platform-based CSS extractors for dealer sites.

Instead of writing one extractor per dealer, we write one per CMS PLATFORM.
Many dealers share the same platform, so one extractor covers many dealers.

Supported platforms:
- Octane: Used by Longo Toyota and similar
- DealerOn/Gemini: Used by Toyota of Downtown LA, North Hollywood Toyota, etc.
- DealerInspire: Used by Airport Marina Honda, Norm Reeves Honda, Culver City Toyota, etc.
"""

import logging
import re
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


# ============================================================
# Shared parsing utilities
# ============================================================

def parse_price(text: str) -> Optional[float]:
    """Extract numeric price from text like '$293' or '$2,931'."""
    if not text:
        return None
    match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', text.replace(',', ''))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_term(text: str) -> Optional[int]:
    """Extract term months from text like '39 Months' or '36 months'."""
    if not text:
        return None
    match = re.search(r'(\d+)\s*months?', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def parse_year_make_model(text: str, default_make: str = "Toyota") -> tuple[Optional[int], str, str, Optional[str]]:
    """
    Parse vehicle info from text like 'New 2026 Toyota Corolla Cross L 2WD (Natl)'.
    Returns: (year, make, model, trim)
    """
    text = text.strip()
    text = re.sub(r'^(new|lease|lease a new|buy a new|lease for)\s+', '', text, flags=re.IGNORECASE)

    year_match = re.search(r'(202[4-7])', text)
    year = int(year_match.group(1)) if year_match else None

    make = default_make
    for m in ["Toyota", "Honda", "Tesla", "Hyundai", "Kia", "Nissan", "Ford", "Chevrolet"]:
        if m.lower() in text.lower():
            make = m
            break

    text = re.sub(r'202[4-7]\s+', '', text)
    text = re.sub(r'(Toyota|Honda|Tesla|Hyundai|Kia|Nissan|Ford|Chevrolet)\s+', '', text, flags=re.IGNORECASE)

    all_models = [
        # Toyota (longer names first)
        "Corolla Cross", "Grand Highlander", "GR Corolla", "GR Supra", "GR86",
        "Land Cruiser", "4Runner", "RAV4", "Camry", "Corolla", "Highlander",
        "Tacoma", "Tundra", "Prius", "Sienna", "Sequoia", "Venza", "Crown",
        "bZ4X", "Mirai",
        # Honda
        "Civic Hybrid", "Civic Hatchback", "CR-V Hybrid", "Accord Hybrid",
        "CR-V", "HR-V", "Civic", "Accord", "Pilot", "Passport",
        "Odyssey", "Ridgeline", "Prologue",
        # Tesla
        "Model 3", "Model Y", "Model S", "Model X", "Cybertruck",
    ]

    model = None
    trim = None

    for m in sorted(all_models, key=len, reverse=True):
        if m.lower() in text.lower():
            model = m
            idx = text.lower().find(m.lower())
            if idx >= 0:
                trim_text = text[idx + len(m):].strip()
                trim_text = re.sub(r'\s*\(.*\)\s*$', '', trim_text)
                trim_text = re.sub(r'\s+\d+WD\s*$', '', trim_text)
                trim_text = re.sub(r'\s*(Sedan|Hatchback|Coupe|SUV)\s*$', '', trim_text, flags=re.IGNORECASE)
                if trim_text:
                    trim = trim_text.strip()
            break

    if not model:
        words = text.split()
        if words:
            model = words[0]

    return year, make, model or "Unknown", trim


def parse_expiration(text: str) -> Optional[str]:
    """Parse expiration date from text."""
    # MM/DD/YYYY
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if match:
        month, day, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    # "through M/DD/YYYY" or "good through"
    match = re.search(r'through\s+(\d{1,2})/(\d{1,2})/(\d{4})', text, re.IGNORECASE)
    if match:
        month, day, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return None


def make_offer_dict(year, make, model, trim, offer_type, monthly_payment,
                    down_payment=None, term_months=None, annual_mileage=None,
                    apr=None, offer_end_date=None, disclaimer=None, image_url=None,
                    confidence=0.85, source_anchor=None):
    """Create a standardized offer dict."""
    return {
        "year": year or datetime.now().year,
        "make": make,
        "model": model,
        "trim": trim,
        "offer_type": offer_type,
        "monthly_payment": monthly_payment,
        "down_payment": down_payment,
        "term_months": term_months or 36,
        "annual_mileage": annual_mileage,
        "apr": apr,
        "msrp": None,
        "selling_price": None,
        "offer_end_date": offer_end_date,
        "disclaimer": disclaimer,
        "confidence": confidence,
        "image_url": image_url,
        "source_anchor": source_anchor,
        "extraction_method": "css",
    }


def dedupe_offers(offers: list[dict]) -> list[dict]:
    """Remove duplicate offers based on year/model/payment."""
    seen = set()
    unique = []
    for o in offers:
        key = (o["year"], o["model"], o["monthly_payment"])
        if key not in seen:
            seen.add(key)
            unique.append(o)
    return unique


# ============================================================
# Platform: Octane (used by Longo Toyota, etc.)
# ============================================================

def extract_octane(html: str, base_url: str = "", default_make: str = "Toyota") -> list[dict]:
    """
    Extract offers from Octane specials platform.

    CSS markers:
    - octane-specials-css-vehicle-title: Vehicle name
    - octane-specials-css-offer-price: Monthly payment or APR
    - octane-specials-css-offer-price-subtext: "/month" or "apr"
    """
    soup = BeautifulSoup(html, "html.parser")
    offers = []

    title_elements = soup.select(
        '.octane-specials-css-vehicle-title, .octane-specials-css-vehicle-slide-title'
    )
    logger.info(f"Octane: Found {len(title_elements)} vehicle titles")

    for title_el in title_elements:
        try:
            vehicle_text = title_el.get_text(strip=True)
            if not vehicle_text or len(vehicle_text) < 5:
                continue

            # Walk up to find parent with pricing
            container = title_el.parent
            for _ in range(10):
                if container is None:
                    break
                if container.select_one('.octane-specials-css-offer-price'):
                    break
                container = container.parent

            if not container:
                continue

            price_el = container.select_one('.octane-specials-css-offer-price')
            price_subtext = container.select_one('.octane-specials-css-offer-price-subtext')
            if not price_el:
                continue

            price_text = price_el.get_text(strip=True)
            subtext = price_subtext.get_text(strip=True).lower() if price_subtext else ""

            if 'apr' in subtext or '%' in price_text:
                offer_type = 'finance'
                apr = parse_price(price_text)
                monthly_payment = None
            else:
                offer_type = 'lease'
                monthly_payment = parse_price(price_text)
                apr = None

            if monthly_payment is None and apr is None:
                continue

            year, make, model, trim = parse_year_make_model(vehicle_text, default_make)
            container_text = container.get_text()

            down_payment = None
            down_match = re.search(r'\$?([\d,]+)\s*(?:due at signing|at signing)', container_text, re.IGNORECASE)
            if down_match:
                down_payment = parse_price(down_match.group(1))

            term_months = parse_term(container_text)

            annual_mileage = None
            mileage_match = re.search(r'(\d{1,2})[,\s]*000\s*miles?', container_text, re.IGNORECASE)
            if mileage_match:
                annual_mileage = int(mileage_match.group(1)) * 1000

            image_url = None
            img = container.select_one('img[src*="vehicle"], img[src*="toyota"], img[alt*="Toyota"]')
            if img:
                src = img.get('src') or img.get('data-src')
                if src:
                    image_url = urljoin(base_url, src)

            # Capture anchor ID from container (e.g. "octane-specials-css-specials-page-offer-12117")
            source_anchor = None
            anchor_el = container if container.get('id') else None
            if not anchor_el:
                # Walk up a few levels to find an element with an id
                parent = container.parent
                for _ in range(3):
                    if parent and parent.get('id'):
                        anchor_el = parent
                        break
                    parent = parent.parent if parent else None
            if anchor_el and anchor_el.get('id'):
                source_anchor = anchor_el['id']

            offers.append(make_offer_dict(
                year, make, model, trim, offer_type, monthly_payment,
                down_payment=down_payment, term_months=term_months,
                annual_mileage=annual_mileage, apr=apr, image_url=image_url,
                source_anchor=source_anchor,
            ))
        except Exception as e:
            logger.warning(f"Octane parse error: {e}")
            continue

    offers = dedupe_offers(offers)
    logger.info(f"Octane extractor: {len(offers)} offers")
    return offers


# ============================================================
# Platform: DealerOn/Gemini (used by Toyota Downtown LA, North Hollywood Toyota, etc.)
# ============================================================

def extract_dealeron_gemini(html: str, base_url: str = "", default_make: str = "Toyota") -> list[dict]:
    """
    Extract offers from DealerOn/Gemini platform.

    CSS markers:
    - vehicle-specials-banner: Offer container
    - vehicle-specials-vehiclename: Vehicle name
    - pricing: Monthly payment
    - terms: Payment terms
    - vehicle-description: Due at signing, expiration
    """
    soup = BeautifulSoup(html, "html.parser")
    offers = []

    specials = soup.select('.vehicle-specials-banner')
    logger.info(f"DealerOn/Gemini: Found {len(specials)} banners")

    for special in specials:
        try:
            name_el = special.select_one('.vehicle-specials-vehiclename')
            if not name_el:
                continue

            vehicle_text = name_el.get_text(strip=True)
            if not vehicle_text or len(vehicle_text) < 5:
                continue

            price_el = special.select_one('.pricing')
            if not price_el:
                continue

            monthly_payment = parse_price(price_el.get_text())
            if not monthly_payment:
                continue

            terms_el = special.select_one('.terms')
            term_months = parse_term(terms_el.get_text()) if terms_el else None

            desc_el = special.select_one('.vehicle-description')
            desc_text = desc_el.get_text() if desc_el else ""

            down_payment = None
            down_match = re.search(r'\$?([\d,]+)\s*(?:due at signing|at signing)', desc_text, re.IGNORECASE)
            if down_match:
                down_payment = parse_price(down_match.group(1))

            expiration = parse_expiration(desc_text)
            year, make, model, trim = parse_year_make_model(vehicle_text, default_make)
            offer_type = 'lease' if 'lease' in vehicle_text.lower() else 'finance'

            image_url = None
            parent = special.parent
            for _ in range(5):
                if parent is None:
                    break
                img = parent.select_one('img.img-fluid, img[src*="secureoffersites"]')
                if img:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        image_url = src if src.startswith('http') else urljoin(base_url, src)
                    break
                parent = parent.parent

            # Capture anchor ID from special container or its parents
            source_anchor = None
            el = special
            for _ in range(5):
                if el is None:
                    break
                if el.get('id'):
                    source_anchor = el['id']
                    break
                el = el.parent

            offers.append(make_offer_dict(
                year, make, model, trim, offer_type, monthly_payment,
                down_payment=down_payment, term_months=term_months,
                offer_end_date=expiration, disclaimer=desc_text[:500] if desc_text else None,
                image_url=image_url, source_anchor=source_anchor,
            ))
        except Exception as e:
            logger.warning(f"DealerOn parse error: {e}")
            continue

    offers = dedupe_offers(offers)
    logger.info(f"DealerOn/Gemini extractor: {len(offers)} offers")
    return offers


# ============================================================
# Platform: DealerInspire (used by Airport Marina Honda, Norm Reeves Honda, Culver City Toyota, etc.)
# ============================================================

def extract_dealerinspire(html: str, base_url: str = "", default_make: str = "Honda") -> list[dict]:
    """
    Extract offers from DealerInspire platform.

    Has two sub-variants:
    1. Structured: Uses <span class="offerrate"> and <span class="offerlabel">
    2. Text-based: All data embedded in paragraph text

    CSS markers:
    - li.special-offer: Offer card container
    - h2 inside container: Vehicle/offer name
    - span.offerrate: Payment (variant 1)
    - span.offerlabel: Down payment/details (variant 1)
    - offer-description: Full text with embedded pricing (variant 2)
    """
    soup = BeautifulSoup(html, "html.parser")
    offers = []

    offer_cards = soup.select('li.special-offer')
    logger.info(f"DealerInspire: Found {len(offer_cards)} offer cards")

    for card in offer_cards:
        try:
            full_text = card.get_text()
            # Capture anchor ID (e.g. "offer-29956" on the <li> element)
            source_anchor = card.get('id')

            # Try structured extraction first (Norm Reeves style)
            offerrate = card.select_one('.offerrate')
            if offerrate:
                offers.extend(_extract_di_structured(card, full_text, base_url, default_make, source_anchor))
            else:
                # Fall back to text-based extraction (Airport Marina style)
                offers.extend(_extract_di_text(card, full_text, base_url, default_make, source_anchor))

        except Exception as e:
            logger.warning(f"DealerInspire parse error: {e}")
            continue

    offers = dedupe_offers(offers)
    logger.info(f"DealerInspire extractor: {len(offers)} offers")
    return offers


def _extract_di_structured(card, full_text: str, base_url: str, default_make: str, source_anchor: str = None) -> list[dict]:
    """DealerInspire variant 1: Structured spans (offerrate, offerlabel)."""
    results = []

    h2 = card.select_one('h2')
    vehicle_text = h2.get_text(strip=True) if h2 else ""

    offerrate = card.select_one('.offerrate')
    rate_text = offerrate.get_text(strip=True) if offerrate else ""

    # Extract monthly payment from "Lease for $259/mo. + tax"
    monthly_payment = None
    payment_match = re.search(r'\$(\d[\d,]*)', rate_text)
    if payment_match:
        monthly_payment = parse_price(payment_match.group(0))

    if not monthly_payment:
        return results

    # Down payment from offerlabel: "$3,500 due at lease signing..."
    offerlabel = card.select_one('.offerlabel')
    label_text = offerlabel.get_text(strip=True) if offerlabel else ""
    down_payment = None
    down_match = re.search(r'\$([\d,]+)\s*(?:due|at)', label_text, re.IGNORECASE)
    if down_match:
        down_payment = parse_price(down_match.group(0))

    # Term from full text: "36 months" or "39 months"
    term_months = parse_term(full_text)

    # Mileage
    annual_mileage = None
    mileage_match = re.search(r'(\d{1,2})[,\s]*000\s*miles?', full_text, re.IGNORECASE)
    if mileage_match:
        annual_mileage = int(mileage_match.group(1)) * 1000

    # Expiration
    expiration = parse_expiration(full_text)

    # Parse vehicle info from h2 text
    year, make, model, trim = parse_year_make_model(vehicle_text, default_make)

    offer_type = 'lease' if 'lease' in rate_text.lower() else 'finance'

    # Image
    image_url = None
    img = card.select_one('img')
    if img:
        src = img.get('src') or img.get('data-src')
        if src and ('dealerinspire' in src or 'vehicle' in src.lower()):
            image_url = src if src.startswith('http') else urljoin(base_url, src)

    disclaimer = full_text[:500].strip() if full_text else None

    results.append(make_offer_dict(
        year, make, model, trim, offer_type, monthly_payment,
        down_payment=down_payment, term_months=term_months,
        annual_mileage=annual_mileage, offer_end_date=expiration,
        disclaimer=disclaimer, image_url=image_url, confidence=0.85,
        source_anchor=source_anchor,
    ))
    return results


def _extract_di_text(card, full_text: str, base_url: str, default_make: str, source_anchor: str = None) -> list[dict]:
    """DealerInspire variant 2: All data in paragraph text."""
    results = []

    # Look for patterns like "Lease for $159 a month" or "$189/mo"
    payment_match = re.search(
        r'(?:lease|finance)\s+(?:for\s+)?\$([\d,]+)\s*(?:a\s*month|/mo|per\s*month)',
        full_text, re.IGNORECASE
    )
    if not payment_match:
        # Also try "$XXX/mo" without "lease for" prefix
        payment_match = re.search(r'\$([\d,]+)\s*/mo', full_text, re.IGNORECASE)

    if not payment_match:
        return results

    monthly_payment = float(payment_match.group(1).replace(',', ''))

    # Vehicle info: Look for "YYYY Honda Model Trim" pattern
    vehicle_match = re.search(
        r'(202[4-7])\s+(?:Honda|Toyota)\s+(\w[\w\s-]*?)(?:\s*:|\s+\d+\s+at)',
        full_text
    )
    if vehicle_match:
        year = int(vehicle_match.group(1))
        vehicle_text = vehicle_match.group(0)
    else:
        # Try the h2 title
        h2 = card.select_one('h2')
        vehicle_text = h2.get_text(strip=True) if h2 else ""
        year_match = re.search(r'(202[4-7])', full_text)
        year = int(year_match.group(1)) if year_match else None

    _, make, model, trim = parse_year_make_model(vehicle_text, default_make)

    # Down payment: "$3,995 cap cost due at signing" or "$X,XXX due at signing"
    down_payment = None
    down_match = re.search(
        r'\$([\d,]+)\s*(?:cap cost\s*)?(?:due at signing|due at lease signing)',
        full_text, re.IGNORECASE
    )
    if down_match:
        down_payment = parse_price(down_match.group(0))

    term_months = parse_term(full_text)

    annual_mileage = None
    mileage_match = re.search(r'(\d{1,2})[,\s]*000\s*miles?\s*per\s*year', full_text, re.IGNORECASE)
    if mileage_match:
        annual_mileage = int(mileage_match.group(1)) * 1000

    expiration = parse_expiration(full_text)

    offer_type = 'lease' if 'lease' in full_text.lower()[:200] else 'finance'

    # Image
    image_url = None
    img = card.select_one('img')
    if img:
        src = img.get('src') or img.get('data-src')
        if src and 'dealerinspire' in src:
            image_url = src if src.startswith('http') else urljoin(base_url, src)

    results.append(make_offer_dict(
        year, make, model, trim, offer_type, monthly_payment,
        down_payment=down_payment, term_months=term_months,
        annual_mileage=annual_mileage, offer_end_date=expiration,
        disclaimer=full_text[:500].strip(), image_url=image_url, confidence=0.80,
        source_anchor=source_anchor,
    ))
    return results


# ============================================================
# Platform detection and routing
# ============================================================

def detect_platform(html: str) -> Optional[str]:
    """Auto-detect which CMS platform a page uses."""
    if "octane-specials-css" in html:
        return "octane"
    if "vehicle-specials-banner" in html and "vehicle-specials-vehiclename" in html:
        return "dealeron_gemini"
    if "special-offer" in html and ("offerrate" in html or "offer-content" in html):
        return "dealerinspire"
    return None


PLATFORM_EXTRACTORS = {
    "octane": extract_octane,
    "dealeron_gemini": extract_dealeron_gemini,
    "dealerinspire": extract_dealerinspire,
}

# Map dealer slugs to platform overrides (if auto-detect isn't reliable)
DEALER_PLATFORM_OVERRIDES = {
    "longo-toyota": "octane",
    "toyota-downtown-la": "dealeron_gemini",
    "north-hollywood-toyota": "dealeron_gemini",
    "culver-city-toyota": "dealerinspire",
    "autonation-toyota-cerritos": "dealerinspire",
    "airport-marina-honda": "dealerinspire",
    "galpin-honda": "dealerinspire",
    "goudy-honda": "dealerinspire",
    "norm-reeves-honda-cerritos": "dealerinspire",
}


def has_css_extractor(dealer_slug: str) -> bool:
    """Check if we can handle this dealer with CSS (via slug override or auto-detect)."""
    return dealer_slug in DEALER_PLATFORM_OVERRIDES


def extract_with_css(dealer_slug: str, html: str, base_url: str = "",
                     default_make: str = "Toyota") -> list[dict]:
    """
    Extract offers using CSS selectors.

    1. Check slug-based platform override
    2. Try auto-detecting platform from HTML
    3. Use appropriate platform extractor
    """
    # Check slug override first
    platform = DEALER_PLATFORM_OVERRIDES.get(dealer_slug)

    # If no override, try auto-detection
    if not platform:
        platform = detect_platform(html)

    if not platform:
        logger.info(f"No CSS extractor for {dealer_slug}")
        return []

    extractor = PLATFORM_EXTRACTORS.get(platform)
    if not extractor:
        return []

    try:
        logger.info(f"Using {platform} extractor for {dealer_slug}")
        return extractor(html, base_url, default_make=default_make)
    except Exception as e:
        logger.error(f"CSS extraction failed for {dealer_slug} ({platform}): {e}")
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_files = [
        ("sample_longo_toyota.html", "longo-toyota", "https://www.longotoyota.com", "Toyota"),
        ("sample_toyota_downtown_la.html", "toyota-downtown-la", "https://www.toyotaofdowntownla.com", "Toyota"),
        ("sample_norm_reeves_honda.html", "norm-reeves-honda-cerritos", "https://www.normreeveshondacerritos.com", "Honda"),
        ("sample_airport_marina_honda.html", "airport-marina-honda", "https://www.airportmarinahonda.com", "Honda"),
    ]

    for filename, slug, url, make in test_files:
        print(f"\n=== {slug} ({make}) ===")
        try:
            with open(filename, "r", encoding="utf-8") as f:
                html = f.read()
            offers = extract_with_css(slug, html, url, default_make=make)
            print(f"Found {len(offers)} offers:")
            for o in offers:
                payment = f"${o['monthly_payment']}/mo" if o['monthly_payment'] else f"{o.get('apr')}% APR"
                down = f" (${o['down_payment']} down)" if o.get('down_payment') else ""
                print(f"  {o['year']} {o['make']} {o['model']} {o.get('trim', '') or ''} - {payment}{down}")
        except FileNotFoundError:
            print(f"  Sample file not found: {filename}")
