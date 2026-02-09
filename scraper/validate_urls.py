"""Validate source URLs and deactivate offers with broken links."""

import asyncio
import httpx
import asyncpg
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Get DATABASE_URL and convert to asyncpg format
DATABASE_URL = os.getenv("DATABASE_URL", "")
# Convert from postgresql+asyncpg:// to postgresql://
DB_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Known bad/sketchy domains to reject
BAD_DOMAINS = [
    "parking.com", "sedoparking.com", "godaddy.com", "hugedomains.com",
    "afternic.com", "dan.com", "sav.com", "bodis.com"
]

# Keywords that suggest a legit dealer specials page
VALID_CONTENT_KEYWORDS = ["special", "lease", "finance", "offer", "msrp", "toyota", "honda"]


async def check_url(client: httpx.AsyncClient, url: str) -> tuple[str, int, bool, str]:
    """
    Check if URL is valid with thorough validation.
    Returns: (url, status_code, is_valid, reason)
    """
    try:
        original_domain = urlparse(url).netloc.lower()

        response = await client.get(url, follow_redirects=True, timeout=15)
        final_url = str(response.url)
        final_domain = urlparse(final_url).netloc.lower()

        # Check 1: HTTP status
        if response.status_code != 200:
            return url, response.status_code, False, f"HTTP {response.status_code}"

        # Check 2: Domain redirect (sketchy sites often redirect)
        if final_domain != original_domain:
            # Allow www prefix changes
            if not (final_domain == f"www.{original_domain}" or original_domain == f"www.{final_domain}"):
                return url, response.status_code, False, f"Redirected to {final_domain}"

        # Check 3: Known bad domains
        for bad in BAD_DOMAINS:
            if bad in final_domain:
                return url, response.status_code, False, f"Parked/spam domain: {bad}"

        # Check 4: Content validation - check if page looks like a dealer specials page
        content = response.text.lower()
        has_valid_content = any(keyword in content for keyword in VALID_CONTENT_KEYWORDS)

        if not has_valid_content:
            return url, response.status_code, False, "No dealer content found"

        # Check 5: Look for 404-like content on 200 pages
        if "page not found" in content or "404" in content[:1000] or "no longer available" in content:
            return url, response.status_code, False, "Soft 404 detected"

        return url, response.status_code, True, "Valid"

    except httpx.TimeoutException:
        return url, 0, False, "Timeout"
    except httpx.ConnectError:
        return url, 0, False, "Connection failed"
    except Exception as e:
        return url, -1, False, f"Error: {str(e)[:50]}"


async def validate_and_cleanup():
    """Check all offer URLs and deactivate broken ones."""

    # Connect to database (disable statement cache for pgbouncer compatibility)
    conn = await asyncpg.connect(DB_URL, statement_cache_size=0)

    # Get unique source URLs with offer count
    rows = await conn.fetch("""
        SELECT source_url, COUNT(*) as offer_count
        FROM offers
        WHERE active = true AND source_url IS NOT NULL
        GROUP BY source_url
    """)
    urls_to_check = [(row['source_url'], row['offer_count']) for row in rows]

    print(f"Checking {len(urls_to_check)} unique URLs ({sum(r[1] for r in urls_to_check)} total offers)...\n")

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        follow_redirects=True
    ) as client:
        tasks = [check_url(client, url) for url, _ in urls_to_check]
        results = await asyncio.gather(*tasks)

    bad_urls = []
    print("Results:")
    print("-" * 70)
    for (url, offer_count), (_, status, is_valid, reason) in zip(urls_to_check, results):
        status_str = "[OK]  " if is_valid else "[BAD] "
        print(f"{status_str} ({offer_count} offers) {reason}")
        print(f"       {url[:65]}...")
        if not is_valid:
            bad_urls.append((url, offer_count, reason))

    print("-" * 70)

    if not bad_urls:
        print("\nAll URLs are valid!")
        await conn.close()
        return

    total_bad_offers = sum(count for _, count, _ in bad_urls)
    print(f"\nFound {len(bad_urls)} bad URLs affecting {total_bad_offers} offers.")
    print("Deactivating...")

    for bad_url, count, reason in bad_urls:
        result = await conn.execute(
            "UPDATE offers SET active = false WHERE source_url = $1 AND active = true",
            bad_url
        )
        actual_count = int(result.split()[-1]) if result else 0
        print(f"  Deactivated {actual_count} offers - {reason}")

    await conn.close()
    print("\nDone! Bad listings have been deactivated.")


async def check_stale_offers(max_age_hours: int = 48):
    """Check for offers that haven't been refreshed recently."""

    conn = await asyncpg.connect(DB_URL, statement_cache_size=0)

    # Find offers older than max_age_hours
    stale = await conn.fetch(f"""
        SELECT o.id, o.model, o.trim, d.name as dealer_name, o.updated_at,
               EXTRACT(EPOCH FROM (NOW() - o.updated_at)) / 3600 as hours_old
        FROM offers o
        JOIN dealers d ON o.dealer_id = d.id
        WHERE o.active = true
          AND o.updated_at < NOW() - INTERVAL '{max_age_hours} hours'
        ORDER BY o.updated_at ASC
    """)

    if not stale:
        print(f"\nNo offers older than {max_age_hours} hours. Data is fresh!")
        await conn.close()
        return

    print(f"\nFound {len(stale)} stale offers (>{max_age_hours}h old):")
    print("-" * 60)
    for row in stale:
        hours = int(row['hours_old'])
        print(f"  {row['model']} {row['trim'] or ''} @ {row['dealer_name']} - {hours}h old")

    # Ask before deactivating
    print(f"\nThese offers may be outdated. Run a fresh scrape to update them.")
    print("To deactivate stale offers, call: deactivate_stale_offers()")

    await conn.close()


async def deactivate_stale_offers(max_age_hours: int = 48):
    """Deactivate offers that are too old."""

    conn = await asyncpg.connect(DB_URL, statement_cache_size=0)

    result = await conn.execute(f"""
        UPDATE offers
        SET active = false
        WHERE active = true
          AND updated_at < NOW() - INTERVAL '{max_age_hours} hours'
    """)

    count = int(result.split()[-1]) if result else 0
    print(f"Deactivated {count} stale offers (>{max_age_hours}h old)")

    await conn.close()


async def full_validation(deactivate_stale: bool = False, stale_hours: int = 48):
    """Run full validation: URL checks + staleness check."""
    print("=" * 60)
    print("FULL OFFER VALIDATION")
    print("=" * 60)

    # Step 1: Validate URLs
    print("\n[1/2] Checking URLs...")
    await validate_and_cleanup()

    # Step 2: Check staleness
    print(f"\n[2/2] Checking for stale offers (>{stale_hours}h)...")
    if deactivate_stale:
        await deactivate_stale_offers(stale_hours)
    else:
        await check_stale_offers(stale_hours)

    print("\n" + "=" * 60)
    print("Validation complete!")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    if "--full" in sys.argv:
        # Full validation with staleness check
        deactivate = "--deactivate-stale" in sys.argv
        asyncio.run(full_validation(deactivate_stale=deactivate))
    elif "--stale" in sys.argv:
        # Just check stale offers
        asyncio.run(check_stale_offers())
    else:
        # Default: just URL validation
        asyncio.run(validate_and_cleanup())
