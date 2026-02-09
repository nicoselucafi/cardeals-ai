"""Intercept API calls from dealer pages to capture offer data."""

import json
import logging
import re
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keywords that suggest an API response contains offer/inventory data
OFFER_KEYWORDS = [
    "payment", "lease", "finance", "apr", "msrp", "price",
    "offer", "incentive", "special", "monthly", "inventory"
]


def intercept_dealer_apis(url: str):
    """
    Load a dealer page and intercept all API responses,
    looking for ones that contain offer/pricing data.
    """
    captured_responses = []

    def handle_response(response):
        """Callback for each network response."""
        url = response.url
        content_type = response.headers.get("content-type", "")

        # Only look at JSON responses
        if "application/json" not in content_type:
            return

        try:
            # Get the response body
            body = response.text()

            # Check if it looks like offer data
            body_lower = body.lower()
            matches = sum(1 for kw in OFFER_KEYWORDS if kw in body_lower)

            if matches >= 2:  # At least 2 keywords match
                logger.info(f"Found potential offer API: {url[:100]}")
                captured_responses.append({
                    "url": url,
                    "status": response.status,
                    "body": body[:5000],  # Truncate for logging
                    "keyword_matches": matches
                })
        except Exception as e:
            pass  # Some responses can't be read as text

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        # Attach response listener
        page.on("response", handle_response)

        logger.info(f"Loading: {url}")

        # Navigate and wait for network to settle
        page.goto(url, wait_until="networkidle", timeout=60000)

        # Scroll to trigger lazy loading
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Wait for any additional API calls
        page.wait_for_timeout(5000)

        browser.close()

    return captured_responses


def main():
    dealers = [
        ("Longo Toyota", "https://www.longotoyota.com/new-toyota-specials-los-angeles.html"),
        ("Toyota Downtown LA", "https://www.toyotaofdowntownla.com/new-vehicle-specials/"),
        ("Toyota Santa Monica", "https://www.santamonicatoyota.com/new-vehicle-specials/"),
    ]

    all_results = {}

    for name, url in dealers:
        print(f"\n{'='*60}")
        print(f"Intercepting APIs for: {name}")
        print(f"{'='*60}")

        responses = intercept_dealer_apis(url)
        all_results[name] = responses

        print(f"\nFound {len(responses)} potential offer API calls")

        for i, resp in enumerate(responses[:5]):  # Show first 5
            print(f"\n--- API {i+1}: {resp['url'][:80]}...")
            print(f"    Status: {resp['status']}, Keywords: {resp['keyword_matches']}")
            # Show snippet of body
            body_preview = resp['body'][:500].replace('\n', ' ')
            print(f"    Preview: {body_preview}...")

    # Save full results
    with open("captured_apis.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nFull results saved to captured_apis.json")


if __name__ == "__main__":
    main()
