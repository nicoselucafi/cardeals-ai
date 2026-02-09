"""Debug script to test extraction on a single dealer."""

import logging
import json
from config import DEALERS, OPENAI_API_KEY
from fetcher import fetch_page
from extractor import extract_offers, clean_html

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Check API key
print("=" * 60)
print("API Key Check")
print("=" * 60)
if OPENAI_API_KEY:
    print(f"OPENAI_API_KEY is set: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}")
else:
    print("ERROR: OPENAI_API_KEY is NOT set!")
    print("Please add it to scraper/.env")
    exit(1)

# Test with first dealer
dealer = DEALERS[0]
print(f"\n{'=' * 60}")
print(f"Testing: {dealer['name']}")
print(f"URL: {dealer['specials_url']}")
print("=" * 60)

# Fetch
print("\n[1] Fetching page...")
html = fetch_page(dealer["specials_url"])
if not html:
    print("FAILED to fetch page")
    exit(1)

print(f"Fetched {len(html):,} bytes")

# Show cleaned text sample
print("\n[2] Cleaned text sample (first 2000 chars):")
text = clean_html(html)
print("-" * 40)
print(text[:2000])
print("-" * 40)
print(f"Total cleaned text length: {len(text):,} chars")

# Extract
print("\n[3] Extracting offers with GPT-4...")
try:
    offers = extract_offers(html, dealer["name"], base_url=dealer["specials_url"])
    print(f"\nExtracted {len(offers)} offers:")
    for i, offer in enumerate(offers[:5], 1):
        print(f"\nOffer {i}:")
        print(json.dumps(offer, indent=2, default=str))
except Exception as e:
    print(f"EXTRACTION ERROR: {e}")
    import traceback
    traceback.print_exc()
