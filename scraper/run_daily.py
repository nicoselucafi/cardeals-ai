"""
Daily scraper script - runs scrape + full validation in one command.
Use this for cron jobs or manual daily runs.

Usage:
    python run_daily.py
"""

import asyncio
import logging
from datetime import datetime

from main import main as run_scrape
from validate_urls import full_validation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("DAILY SCRAPER RUN")
    logger.info(f"Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Step 1: Run the scraper
    logger.info("\n[STEP 1/2] Scraping dealer offers...")
    run_scrape()

    # Step 2: Run full validation with stale cleanup
    logger.info("\n[STEP 2/2] Validating URLs and cleaning stale offers...")
    asyncio.run(full_validation(deactivate_stale=True, stale_hours=48))

    end = datetime.now()
    duration = (end - start).total_seconds()

    logger.info("\n" + "=" * 60)
    logger.info(f"DAILY RUN COMPLETE")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
