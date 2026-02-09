"""Scan dealer websites to identify their CMS platform and check for specials."""

import logging
from bs4 import BeautifulSoup
from fetcher import fetch_page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def identify_platform(html: str) -> dict:
    """Identify the dealer CMS platform from HTML markers."""
    platforms = {
        "octane": "octane-specials-css" in html,
        "dealeron_gemini": "vehicle-specials-banner" in html and "vehicle-specials-vehiclename" in html,
        "dealer_com": "ddc-content" in html or "ddc-page" in html,
        "dealer_inspire": "dealerinspire" in html.lower() or "dealer-inspire" in html.lower(),
        "shift_digital": "shiftdigital" in html.lower(),
        "autonation": "autonation" in html.lower() and "specials" in html.lower(),
    }

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text().lower()
    has_lease = "lease" in text or "/mo" in text or "per month" in text
    has_prices = "$" in text and ("month" in text or "/mo" in text)

    offer_count = 0
    for keyword in ["$", "/mo", "per month", "lease", "due at signing"]:
        offer_count += text.count(keyword)

    detected = [name for name, found in platforms.items() if found]

    return {
        "platforms": detected,
        "has_lease_offers": has_lease,
        "has_prices": has_prices,
        "offer_indicator_count": offer_count,
        "page_size": len(html),
    }


# Verified dealer URLs from web search
DEALERS_TO_SCAN = [
    # Toyota
    ("https://www.northhollywoodtoyota.com/new-vehicle-specials/", "North Hollywood Toyota", "Toyota"),
    ("https://www.toyotasantamonica.com/offers-incentives-2/", "Toyota Santa Monica", "Toyota"),
    ("https://www.culvercitytoyota.com/new-vehicles/new-vehicle-specials/", "Culver City Toyota", "Toyota"),
    ("https://www.toyotaofglendale.com/new-monthly-specials/", "Toyota of Glendale", "Toyota"),
    ("https://www.toyotapasadena.com/new-vehicles/new-vehicle-specials/", "Toyota Pasadena", "Toyota"),
    ("https://www.autonationtoyotacerritos.com/toyota-specials.htm", "AutoNation Toyota Cerritos", "Toyota"),
    ("https://www.torrancetoyota.com/promotions/new/index.htm", "DCH Toyota of Torrance", "Toyota"),
    ("https://www.southbaytoyota.com/new-vehicles/new-vehicle-specials/", "South Bay Toyota", "Toyota"),
    ("https://www.norwalktoyota.com/specials/", "Norwalk Toyota", "Toyota"),
    ("https://www.toyotaofglendora.com/specials/vehicle-specials", "Toyota of Glendora", "Toyota"),
    # Honda
    ("https://www.airportmarinahonda.com/new-vehicle-specials-2/", "Airport Marina Honda", "Honda"),
    ("https://www.galpinhonda.com/new-specials/", "Galpin Honda", "Honda"),
    ("https://www.hondaofpasadena.com/new-specials/", "Honda of Pasadena", "Honda"),
    ("https://www.goudyhonda.com/new-vehicles/new-vehicle-specials/", "Goudy Honda", "Honda"),
    ("https://www.normreeveshondacerritos.com/new-vehicles/new-vehicle-specials/", "Norm Reeves Honda Cerritos", "Honda"),
    ("https://www.carsonhonda.net/promotions/new/index.htm", "Carson Honda", "Honda"),
    ("https://www.hondaoflosangeles.com/honda-specials-los-angeles-ca-dtw", "Honda of Downtown LA", "Honda"),
    ("https://scottrobinsonhonda.com/offers/", "Scott Robinson Honda", "Honda"),
]


if __name__ == "__main__":
    print(f"Scanning {len(DEALERS_TO_SCAN)} dealer websites...\n")

    results = []
    for url, name, make in DEALERS_TO_SCAN:
        print(f"--- {name} ({make}) ---")
        print(f"  URL: {url}")

        html = fetch_page(url)
        if not html:
            print(f"  FAILED to fetch\n")
            results.append((name, make, url, "FAILED", {}))
            continue

        info = identify_platform(html)
        platform_str = ", ".join(info["platforms"]) if info["platforms"] else "unknown"
        print(f"  Platform: {platform_str}")
        print(f"  Has offers: {info['has_lease_offers']} | Has prices: {info['has_prices']}")
        print(f"  Offer indicators: {info['offer_indicator_count']} | Page size: {info['page_size']:,}")
        print()

        results.append((name, make, url, platform_str, info))

    # Summary
    print("\n" + "=" * 70)
    print("RESULTS BY PLATFORM")
    print("=" * 70)

    for name, make, url, platform, info in results:
        if platform == "FAILED":
            status = "FAILED"
        elif info.get("has_prices"):
            status = "HAS PRICES"
        elif info.get("has_lease_offers"):
            status = "HAS OFFERS (no prices?)"
        else:
            status = "NO OFFERS"
        print(f"  [{platform:20s}] {status:25s} {name} ({make})")
