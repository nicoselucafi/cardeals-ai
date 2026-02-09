"""Fetch dealer specials pages via requests or Playwright."""

import logging
import time
from typing import Optional

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from config import USER_AGENT, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


def fetch_with_requests(url: str) -> Optional[str]:
    """
    Fetch page HTML using requests library.
    Returns HTML string or None on failure.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # Check content length
        content = response.text
        if len(content) < 1000:
            logger.warning(f"Response too short ({len(content)} bytes), may be blocked")
            return None

        logger.info(f"Fetched {len(content):,} bytes via requests")
        return content

    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error {e.response.status_code}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request failed: {e}")
        return None


def fetch_with_playwright(url: str) -> Optional[str]:
    """
    Fetch page HTML using Playwright headless browser.
    Fallback for JavaScript-rendered pages.
    Returns HTML string or None on failure.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080},
            )
            page = context.new_page()

            # Navigate and wait for network to be idle
            page.goto(url, wait_until="networkidle", timeout=REQUEST_TIMEOUT * 1000)

            # Wait for dynamic content - reduced timeouts for faster scraping
            try:
                page.wait_for_selector(
                    "[class*='special'], [class*='offer'], [class*='price'], [class*='payment'], [class*='lease']",
                    timeout=5000
                )
                logger.info("Found offer-related elements on page")
            except Exception:
                logger.debug("No specific offer selectors found, continuing...")

            # Brief wait for lazy-loaded content
            time.sleep(3)

            # Quick scroll to trigger lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)

            content = page.content()
            browser.close()

            if len(content) < 1000:
                logger.warning(f"Playwright response too short ({len(content)} bytes)")
                return None

            logger.info(f"Fetched {len(content):,} bytes via Playwright")
            return content

    except PlaywrightTimeout:
        logger.error(f"Playwright timeout for {url}")
        return None
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        return None


def fetch_page(url: str, use_playwright_first: bool = True) -> Optional[str]:
    """
    Fetch page HTML, using Playwright by default for JS-heavy dealer sites.

    Args:
        url: The URL to fetch
        use_playwright_first: If True (default), use Playwright for JS rendering

    Returns:
        HTML string or None if all methods fail
    """
    logger.info(f"Fetching: {url}")

    if use_playwright_first:
        # Use Playwright first for dealer sites (they're mostly JS-rendered)
        html = fetch_with_playwright(url)
        if html:
            return html
        logger.info("Playwright failed, trying requests...")
        # Fallback to requests
        html = fetch_with_requests(url)
        if html:
            return html
    else:
        # Try requests first (faster but won't get JS content)
        html = fetch_with_requests(url)
        if html:
            return html
        logger.info("Requests failed, falling back to Playwright...")
        html = fetch_with_playwright(url)
        if html:
            return html

    logger.error(f"All fetch methods failed for {url}")
    return None


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    test_url = "https://www.longotoyota.com/new-vehicle-specials/"
    html = fetch_page(test_url)
    if html:
        print(f"Successfully fetched {len(html):,} bytes")
        print(f"First 500 chars: {html[:500]}")
    else:
        print("Failed to fetch page")
