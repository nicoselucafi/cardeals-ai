"""Analyze DealerInspire HTML structure for CSS extractor."""

import logging
from bs4 import BeautifulSoup
from fetcher import fetch_page

logging.basicConfig(level=logging.INFO)

urls = [
    ("https://www.airportmarinahonda.com/new-vehicle-specials-2/", "Airport Marina Honda"),
    ("https://www.normreeveshondacerritos.com/new-vehicles/new-vehicle-specials/", "Norm Reeves Honda"),
]

for url, name in urls:
    print(f"\n{'='*60}")
    print(f"Analyzing: {name}")
    print(f"{'='*60}")

    html = fetch_page(url)
    if not html:
        print("FAILED")
        continue

    soup = BeautifulSoup(html, "html.parser")

    # Save for reference
    filename = f"sample_{name.lower().replace(' ', '_')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    # Find offer-related containers
    patterns = [
        "[class*='special']", "[class*='offer']", "[class*='payment']",
        "[class*='lease']", "[class*='vehicle']", "[class*='incentive']",
        "[class*='deal']", "[class*='price']", "[class*='promo']",
    ]

    print("\n--- KEY CONTAINERS ---")
    for pattern in patterns:
        elements = soup.select(pattern)
        if elements and len(elements) < 50:
            print(f"\n{pattern}: {len(elements)} elements")
            for el in elements[:3]:
                classes = el.get('class', [])
                tag = el.name
                text = el.get_text()[:100].strip().replace('\n', ' ')
                print(f"  <{tag} class=\"{' '.join(classes)}\"> {text}")

    # Find price elements
    print("\n--- PRICES ---")
    for el in soup.find_all(string=lambda s: s and '$' in s and 'month' in s.lower()):
        parent = el.parent
        if parent:
            classes = parent.get('class', [])
            print(f"  <{parent.name} class=\"{' '.join(classes)}\"> {el.strip()[:80]}")

    # Find vehicle names
    print("\n--- VEHICLE NAMES ---")
    for keyword in ['Civic', 'CR-V', 'Accord', 'Pilot', 'HR-V', 'Corolla', 'RAV4', 'Camry']:
        elements = soup.find_all(string=lambda s, k=keyword: s and k in s)
        if elements:
            for el in elements[:2]:
                p = el.parent
                if p:
                    print(f"  [{keyword}] <{p.name} class=\"{' '.join(p.get('class', []))}\"> {el.strip()[:60]}")
