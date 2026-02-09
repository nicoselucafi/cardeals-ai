"""Analyze dealer HTML structure to build CSS selectors."""

import logging
from bs4 import BeautifulSoup
from fetcher import fetch_page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_page(url: str, name: str):
    """Fetch and analyze a dealer page structure."""
    print(f"\n{'='*60}")
    print(f"Analyzing: {name}")
    print(f"URL: {url}")
    print("="*60)

    html = fetch_page(url)
    if not html:
        print("Failed to fetch page!")
        return

    soup = BeautifulSoup(html, "html.parser")

    # Look for offer-related containers
    offer_patterns = [
        "[class*='special']",
        "[class*='offer']",
        "[class*='deal']",
        "[class*='incentive']",
        "[class*='payment']",
        "[class*='lease']",
        "[class*='vehicle']",
        "[class*='inventory']",
        "[class*='srp-']",
        "[class*='card']",
    ]

    print("\n--- OFFER CONTAINERS ---")
    for pattern in offer_patterns:
        elements = soup.select(pattern)
        if elements:
            print(f"\n{pattern}: {len(elements)} elements")
            for el in elements[:2]:  # First 2
                classes = el.get('class', [])
                tag = el.name
                text_preview = el.get_text()[:100].strip().replace('\n', ' ')
                print(f"  <{tag} class=\"{' '.join(classes)}\">")
                print(f"    Text: {text_preview}...")

    # Look for price patterns
    print("\n--- PRICE ELEMENTS ---")
    price_elements = soup.find_all(string=lambda s: s and ('$' in s or '/mo' in s.lower()))
    for el in price_elements[:10]:
        text = el.strip()[:80]
        parent = el.parent
        if parent:
            print(f"  <{parent.name} class=\"{' '.join(parent.get('class', []))}\"> {text}")

    # Look for vehicle titles/names
    print("\n--- VEHICLE NAMES ---")
    vehicle_keywords = ['RAV4', 'Camry', 'Corolla', 'Tacoma', 'Highlander', 'Prius', '4Runner', 'Tundra', 'Sienna']
    for keyword in vehicle_keywords:
        elements = soup.find_all(string=lambda s: s and keyword in s)
        if elements:
            print(f"\n{keyword} found in {len(elements)} elements:")
            for el in elements[:2]:
                parent = el.parent
                if parent:
                    classes = parent.get('class', [])
                    print(f"  <{parent.name} class=\"{' '.join(classes)}\"> {el.strip()[:60]}")

    # Save sample HTML for manual inspection
    filename = f"sample_{name.lower().replace(' ', '_')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nSaved full HTML to: {filename}")


if __name__ == "__main__":
    dealers = [
        ("https://www.longotoyota.com/new-toyota-specials-los-angeles.html", "Longo Toyota"),
        ("https://www.toyotaofdowntownla.com/new-vehicle-specials/", "Toyota Downtown LA"),
    ]

    for url, name in dealers:
        analyze_page(url, name)
