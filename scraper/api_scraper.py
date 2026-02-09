"""Fetch offers directly from dealer APIs discovered via network interception."""

import json
import logging
import re
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discovered API endpoints for each dealer
DEALER_APIS = {
    "longo-toyota": {
        "specials_api": "https://nitro.octanemarketing.com/get-specials?id=40&only_widget=off&only_special=on&only_slider=off",
        "type": "octane"
    },
}


def parse_octane_html(html: str) -> list[dict]:
    """
    Parse Octane Marketing specials HTML response into structured offers.

    Structure:
    - Each vehicle is in a div with id="octane-specials-css-specials-page-offer-{id}"
    - Vehicle title in h2.octane-specials-css-vehicle-title
    - MSRP in div.octane-specials-css-vehicle-detail containing "SRP"
    - Offers in a.octane-specials-css-special-offer-block elements
    """
    soup = BeautifulSoup(html, "html.parser")
    offers = []

    # Find all vehicle blocks (they have IDs like "octane-specials-css-specials-page-offer-12117")
    vehicle_blocks = soup.find_all(id=re.compile(r"octane-specials-css-specials-page-offer-\d+"))
    logger.info(f"Found {len(vehicle_blocks)} vehicle blocks")

    for block in vehicle_blocks:
        # Get vehicle title (e.g., "New 2026 Toyota Corolla SE")
        title_elem = block.find(class_="octane-specials-css-vehicle-title")
        if not title_elem:
            continue

        title = title_elem.get_text(strip=True)
        logger.info(f"Processing: {title}")

        # Parse year, model, trim from title
        year_match = re.search(r"20\d{2}", title)
        year = int(year_match.group()) if year_match else None

        # Remove "New", year, "Toyota" to get model+trim
        clean_title = re.sub(r"New\s*", "", title, flags=re.I)
        clean_title = re.sub(r"20\d{2}\s*", "", clean_title)
        clean_title = re.sub(r"Toyota\s*", "", clean_title, flags=re.I).strip()
        parts = clean_title.split()
        model = parts[0] if parts else None
        trim = " ".join(parts[1:]) if len(parts) > 1 else None

        # Get vehicle image URL
        image_url = None
        image_elem = block.find("img", class_=re.compile(r"octane.*vehicle.*image|vehicle-slide-image", re.I))
        if image_elem and image_elem.get("src"):
            image_url = image_elem["src"]
            logger.info(f"  Found image: {image_url[:60]}...")

        # Get MSRP from vehicle details
        msrp = None
        details = block.find_all(class_="octane-specials-css-vehicle-detail")
        for detail in details:
            text = detail.get_text(strip=True)
            if "SRP" in text or "MSRP" in text:
                price_match = re.search(r"\$([\d,]+)", text)
                if price_match:
                    msrp = float(price_match.group(1).replace(",", ""))
                    break

        # Find all offer blocks within this vehicle
        offer_blocks = block.find_all(class_="octane-specials-css-special-offer-block")

        for offer_block in offer_blocks:
            offer = {
                "year": year,
                "make": "Toyota",
                "model": model,
                "trim": trim,
                "offer_type": None,
                "monthly_payment": None,
                "down_payment": None,
                "term_months": None,
                "annual_mileage": None,
                "apr": None,
                "msrp": msrp,
                "selling_price": None,
                "offer_end_date": None,
                "disclaimer": None,
                "confidence": 0.9,
                "image_url": image_url
            }

            # Determine offer type from tag
            tag_elem = offer_block.find(class_="octane-specials-css-offer-tag")
            if tag_elem:
                tag_text = tag_elem.get_text(strip=True).lower()
                if "lease" in tag_text:
                    offer["offer_type"] = "lease"
                elif "finance" in tag_text or "apr" in tag_text:
                    offer["offer_type"] = "finance"
                elif "cash" in tag_text or "purchase" in tag_text:
                    offer["offer_type"] = "purchase"

            # Get price element
            price_elem = offer_block.find(class_="octane-specials-css-offer-price")
            if price_elem:
                price_text = price_elem.get_text(strip=True)

                if offer["offer_type"] == "finance":
                    # APR: "4.99%"
                    apr_match = re.search(r"([\d.]+)%", price_text)
                    if apr_match:
                        offer["apr"] = float(apr_match.group(1))
                else:
                    # Monthly payment: "$249"
                    payment_match = re.search(r"\$?([\d,]+)", price_text)
                    if payment_match:
                        offer["monthly_payment"] = float(payment_match.group(1).replace(",", ""))

            # Get offer details from the div-block-24 section
            details_div = offer_block.find(class_=re.compile(r"div-block-24|offer_"))
            if details_div:
                details_text = details_div.get_text(separator="\n", strip=True)

                # Term: "39-month lease" or "Terms up to 72 months"
                term_match = re.search(r"(\d+)[\s-]*month", details_text, re.I)
                if term_match:
                    offer["term_months"] = int(term_match.group(1))

                # Mileage: "10,000 miles per year"
                miles_match = re.search(r"([\d,]+)\s*miles?\s*(?:per\s*year)?", details_text, re.I)
                if miles_match:
                    offer["annual_mileage"] = int(miles_match.group(1).replace(",", ""))

                # Down payment: "$2,999 due at signing" - must have "due" or "signing"
                down_match = re.search(r"\$([\d,]+)\s*(?:due|at\s*signing)", details_text, re.I)
                if down_match:
                    offer["down_payment"] = float(down_match.group(1).replace(",", ""))

                # APR for finance offers (in case not found in price)
                if offer["offer_type"] == "finance" and not offer["apr"]:
                    apr_match = re.search(r"([\d.]+)%\s*APR", details_text, re.I)
                    if apr_match:
                        offer["apr"] = float(apr_match.group(1))

            # Only add if we have meaningful data
            if offer["model"] and (offer["monthly_payment"] or offer["apr"]):
                offers.append(offer)
                logger.info(
                    f"  Parsed {offer['offer_type']}: "
                    f"${offer['monthly_payment']}/mo" if offer['monthly_payment'] else f"{offer['apr']}% APR"
                )

    return offers


def fetch_octane_specials(api_url: str) -> list[dict]:
    """
    Fetch specials from Octane Marketing API.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/json,*/*",
        "Referer": "https://www.longotoyota.com/"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()

        content = response.text
        logger.info(f"Fetched {len(content):,} bytes from Octane API")

        # API returns JSON with html field
        try:
            data = json.loads(content)
            html = data.get("html", content)
        except json.JSONDecodeError:
            html = content

        # Parse the HTML
        offers = parse_octane_html(html)
        return offers

    except Exception as e:
        logger.error(f"Octane API error: {e}")
        return []


def scrape_dealer_api(dealer_slug: str) -> list[dict]:
    """
    Scrape offers from a dealer's API if we have it mapped.
    """
    if dealer_slug not in DEALER_APIS:
        logger.warning(f"No API mapping for {dealer_slug}")
        return []

    api_config = DEALER_APIS[dealer_slug]

    if api_config["type"] == "octane":
        return fetch_octane_specials(api_config["specials_api"])

    return []


def main():
    """Test the API scraper."""
    print("=" * 60)
    print("API-Based Offer Scraper")
    print("=" * 60)

    for dealer_slug in DEALER_APIS:
        print(f"\nScraping: {dealer_slug}")
        print("-" * 40)

        offers = scrape_dealer_api(dealer_slug)

        print(f"\nFound {len(offers)} offers:")
        for offer in offers:
            if offer['offer_type'] == 'lease':
                print(f"  LEASE: {offer['year']} {offer['model']} {offer['trim']}: "
                      f"${offer['monthly_payment']}/mo, {offer['term_months']}mo, "
                      f"${offer['down_payment']} down, MSRP ${offer['msrp']}")
            elif offer['offer_type'] == 'finance':
                print(f"  FINANCE: {offer['year']} {offer['model']} {offer['trim']}: "
                      f"{offer['apr']}% APR, {offer['term_months']}mo")
            else:
                print(f"  {offer['offer_type'].upper()}: {offer['year']} {offer['model']} {offer['trim']}")

        # Save to JSON for inspection
        output_file = f"{dealer_slug}_offers.json"
        with open(output_file, "w") as f:
            json.dump(offers, f, indent=2)
        print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
