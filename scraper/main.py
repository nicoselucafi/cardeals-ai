"""Main scraper entry point."""

import logging
import sys
from datetime import datetime

from config import DEALERS, LOG_LEVEL
from fetcher import fetch_page
from extractor import extract_offers
from validators import validate_offer, clean_offer
from saver import save_offers

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def scrape_dealer(dealer: dict) -> dict:
    """
    Scrape a single dealer's specials page.

    Returns:
        Dict with results: {
            name: str,
            status: 'success' | 'failed',
            fetched: int,
            extracted: int,
            valid: int,
            saved: int,
            error: str | None
        }
    """
    result = {
        "name": dealer["name"],
        "status": "failed",
        "fetched": 0,
        "extracted": 0,
        "valid": 0,
        "saved": 0,
        "error": None,
    }

    try:
        # 1. Fetch page
        logger.info(f"Scraping {dealer['name']} ({dealer['specials_url']})...")
        html = fetch_page(dealer["specials_url"])

        if not html:
            result["error"] = "Failed to fetch page"
            logger.error(f"{dealer['name']}: {result['error']}")
            return result

        result["fetched"] = len(html)
        logger.info(f"Fetched {len(html):,} bytes")

        # 2. Extract offers (CSS first, then GPT-4 fallback)
        raw_offers = extract_offers(
            html,
            dealer["name"],
            base_url=dealer["specials_url"],
            dealer_slug=dealer["slug"],
            default_make=dealer.get("make", "Toyota"),
        )
        result["extracted"] = len(raw_offers)

        if not raw_offers:
            result["error"] = "No offers extracted"
            logger.warning(f"{dealer['name']}: {result['error']}")
            # Still mark as success if we fetched but found no offers
            result["status"] = "success"
            return result

        logger.info(f"Extracted {len(raw_offers)} raw offers")

        # 3. Validate and clean offers
        valid_offers = []
        for offer in raw_offers:
            is_valid, errors = validate_offer(offer)
            if is_valid:
                cleaned = clean_offer(offer)
                valid_offers.append(cleaned)
            else:
                logger.debug(f"Invalid offer: {errors}")

        result["valid"] = len(valid_offers)
        logger.info(f"Validated: {len(valid_offers)} passed, {len(raw_offers) - len(valid_offers)} failed")

        if not valid_offers:
            result["error"] = "No valid offers after validation"
            result["status"] = "success"  # Still fetched and extracted
            return result

        # 4. Save to database (pass full dealer info for auto-creation)
        stats = save_offers(dealer, valid_offers, dealer["specials_url"])
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
        dealer_slugs: List of dealer slugs to scrape. If None, scrape all.
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"Scraper Run Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Filter dealers if specific slugs provided
    if dealer_slugs:
        dealers_to_scrape = [d for d in DEALERS if d["slug"] in dealer_slugs]
    else:
        dealers_to_scrape = DEALERS

    if not dealers_to_scrape:
        logger.error("No dealers to scrape")
        return

    logger.info(f"Scraping {len(dealers_to_scrape)} dealer(s)")

    # Scrape each dealer with delay between requests
    from config import DELAY_BETWEEN_DEALERS
    import time

    results = []
    for i, dealer in enumerate(dealers_to_scrape):
        result = scrape_dealer(dealer)
        results.append(result)

        # Add delay between dealers (except for last one)
        if i < len(dealers_to_scrape) - 1:
            logger.info(f"Waiting {DELAY_BETWEEN_DEALERS}s before next dealer...")
            time.sleep(DELAY_BETWEEN_DEALERS)

    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n")
    print("=" * 60)
    print(f"Scraper Run Complete ({end_time.strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 60)

    total_saved = 0
    failed = 0

    for r in results:
        status_icon = "[OK]" if r["status"] == "success" else "[FAIL]"
        if r["status"] == "success":
            print(f"  {status_icon} {r['name']}: {r['saved']} offers saved")
            total_saved += r["saved"]
        else:
            print(f"  {status_icon} {r['name']}: Failed ({r['error']})")
            failed += 1

    print("-" * 60)
    print(f"Total: {total_saved} offers saved, {failed} dealer(s) failed")
    print(f"Duration: {duration:.1f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    # Usage: python main.py [dealer-slug ...]
    # No args = scrape ALL dealers

    if len(sys.argv) > 1:
        # Scrape specific dealers
        main(sys.argv[1:])
    else:
        # Scrape all dealers
        main()
