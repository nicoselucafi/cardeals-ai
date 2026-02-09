"""Main script to scrape real offers and save to database."""

import logging
import sys
from datetime import datetime

from api_scraper import scrape_dealer_api, DEALER_APIS
from saver import save_offers
from config import DEALERS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def scrape_and_save_dealer(dealer: dict) -> dict:
    """
    Scrape offers from a dealer's API and save to database.

    Returns:
        Dict with results
    """
    result = {
        "name": dealer["name"],
        "status": "failed",
        "scraped": 0,
        "saved": 0,
        "error": None,
    }

    slug = dealer["slug"]

    # Check if we have an API for this dealer
    if slug not in DEALER_APIS:
        result["error"] = f"No API mapping for {slug}"
        logger.warning(result["error"])
        return result

    try:
        # 1. Scrape offers from API
        logger.info(f"Scraping {dealer['name']}...")
        offers = scrape_dealer_api(slug)
        result["scraped"] = len(offers)

        if not offers:
            result["error"] = "No offers found"
            result["status"] = "success"  # Not an error, just no current offers
            return result

        logger.info(f"Scraped {len(offers)} offers from {dealer['name']}")

        # 2. Save to database
        stats = save_offers(slug, offers, dealer["specials_url"])
        result["saved"] = stats["inserted"]
        result["status"] = "success"

        logger.info(f"Saved {stats['inserted']} offers for {dealer['name']}")

    except Exception as e:
        result["error"] = str(e)
        logger.exception(f"Error scraping {dealer['name']}: {e}")

    return result


def main(dealer_slugs: list[str] = None):
    """
    Main scraper function.

    Args:
        dealer_slugs: List of dealer slugs to scrape. If None, scrape all with APIs.
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"Real Offer Scraper Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Filter dealers
    if dealer_slugs:
        dealers_to_scrape = [d for d in DEALERS if d["slug"] in dealer_slugs]
    else:
        # Only scrape dealers we have API mappings for
        dealers_to_scrape = [d for d in DEALERS if d["slug"] in DEALER_APIS]

    if not dealers_to_scrape:
        logger.error("No dealers to scrape (no API mappings available)")
        return

    logger.info(f"Scraping {len(dealers_to_scrape)} dealer(s)")

    # Scrape each dealer
    results = []
    for dealer in dealers_to_scrape:
        result = scrape_and_save_dealer(dealer)
        results.append(result)

    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n")
    print("=" * 60)
    print(f"Scraper Run Complete ({end_time.strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 60)

    total_scraped = 0
    total_saved = 0
    failed = 0

    for r in results:
        status_icon = "[OK]" if r["status"] == "success" else "[FAIL]"
        if r["status"] == "success":
            print(f"  {status_icon} {r['name']}: {r['scraped']} scraped, {r['saved']} saved")
            total_scraped += r["scraped"]
            total_saved += r["saved"]
        else:
            print(f"  {status_icon} {r['name']}: Failed ({r['error']})")
            failed += 1

    print("-" * 60)
    print(f"Total: {total_scraped} scraped, {total_saved} saved, {failed} failed")
    print(f"Duration: {duration:.1f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        # Default: scrape all dealers with API mappings
        main()
