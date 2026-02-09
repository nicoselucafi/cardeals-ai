Car Deals AI Agent — PLAN.md
Build Phases Overview
PhaseWhatEstimated TimeCheckpoint1Backend API + DatabaseDay 1Can hit /api/health and get JSON back2Scraper for 1 dealerDay 2Real offers from Longo Toyota in database3Scraper for all 5 dealersDay 315+ real offers across 5 dealers4AI Chat AgentDay 4"RAV4 lease under $350" returns real results via API5FrontendDay 5-6Can type query in browser, see offer cards6Connect + PolishDay 6-7Full end-to-end working demo7DeployDay 7Live on the internet, accessible by URL

Phase 1: Backend API + Database
Goal: Working FastAPI server with database tables created and seeded with test data.
Tasks

 1.1 — Initialize backend project

Create backend/ directory
Create requirements.txt with:



    fastapi==0.109.0
    uvicorn[standard]==0.27.0
    sqlalchemy[asyncio]==2.0.25
    asyncpg==0.29.0
    pydantic==2.5.3
    pydantic-settings==2.1.0
    python-dotenv==1.0.0
    openai==1.12.0
    httpx==0.26.0
    cachetools==5.3.2
    sentry-sdk[fastapi]==1.40.0

Create backend/.env with placeholder values
Verify: pip install -r requirements.txt succeeds
 1.2 — Database setup

Create backend/config.py — loads env vars with pydantic-settings
Create backend/database.py — async SQLAlchemy engine + session factory
Create backend/models.py — SQLAlchemy ORM models matching the schema in CLAUDE.md:

Dealer model with all fields
Offer model with all fields + relationship to Dealer
User model (minimal)
SearchLog model


Create Alembic migration OR a create_tables.py script that creates all tables
Verify: Tables exist in database (check with \dt or a test query)


 1.3 — Pydantic schemas

Create backend/schemas.py with:

OfferResponse — what the API returns for an offer
OfferDetailResponse — full detail with raw_extracted_data
SearchParams — query parameters for offer search
ChatRequest — { message: str, conversation_id: Optional[str] }
ChatResponse — { response: str, offers: List[OfferResponse], search_params: dict }
HealthResponse — { status: str, offers_count: int, dealers_count: int, last_scrape: Optional[datetime] }
DealerResponse — dealer info for display




 1.4 — API endpoints (skeleton)

Create backend/main.py:

FastAPI app with CORS middleware (allow frontend origins)
Include routers from api/
Startup event: verify database connection


Create backend/api/health.py:

GET /api/health → returns offer count, dealer count, last scrape time


Create backend/api/offers.py:

GET /api/offers/search → accepts SearchParams, queries database, returns offers
GET /api/offers/{offer_id} → returns single offer detail


Create backend/api/chat.py:

POST /api/chat → placeholder that returns {"response": "Chat coming in Phase 4"}


Verify: uvicorn main:app --reload starts, /api/health returns JSON, /docs shows Swagger UI


 1.5 — Seed data

Create backend/seed.py that:

Inserts 5 real Toyota dealers from the dealer list in CLAUDE.md
Inserts 10-15 realistic sample offers (manually created, realistic prices):

2025 RAV4 LE lease: $299/mo, $3,499 down, 36mo, 12K mi/yr
2025 Camry LE lease: $279/mo, $2,999 down, 36mo, 12K mi/yr
2025 Corolla LE lease: $219/mo, $2,499 down, 36mo, 12K mi/yr
2025 Highlander LE lease: $389/mo, $3,999 down, 36mo, 12K mi/yr
2025 Tacoma SR lease: $329/mo, $3,499 down, 36mo, 12K mi/yr
(create 2-3 offers per dealer with slight price variations)


Sets confidence_score to 1.0 for seed data (manually verified)
Sets extraction_method to "manual_seed"


Verify: /api/offers/search returns seeded offers, /api/offers/search?model=RAV4 filters correctly


 1.6 — Search logic

Create backend/services/offer_search.py:

Query builder that applies filters: model, max_monthly_payment, offer_type, max_down_payment, term range
Sorting: by monthly_payment ASC (default), or confidence_score DESC
Limit: default 10, max 50
Only returns active offers
Joins with Dealer table to include dealer_name, dealer_city in response


Create backend/services/cache.py:

TTLCache wrapper (maxsize=500, ttl=3600)
get_cache_key() function
search_offers_cached() function
invalidate_all_caches() function


Verify: Search returns correct results, caching works (second identical request is faster)



Phase 1 Checkpoint
bash# All of these should work:
curl http://localhost:8000/api/health
# → {"status":"ok","offers_count":15,"dealers_count":5,"last_scrape":null}

curl http://localhost:8000/api/offers/search?model=RAV4
# → {"offers":[...], "total": 3, "filters_applied": {"model":"RAV4"}}

curl http://localhost:8000/api/offers/search?max_monthly_payment=300
# → Returns only offers under $300/mo

curl http://localhost:8000/docs
# → Swagger UI loads with all endpoints documented

Phase 2: Scraper for 1 Dealer
Goal: Successfully scrape Longo Toyota's specials page and extract real offers into the database.
Tasks

 2.1 — Initialize scraper project

Create scraper/ directory
Create scraper/requirements.txt:



    requests==2.31.0
    beautifulsoup4==4.12.3
    openai==1.12.0
    sqlalchemy==2.0.25
    psycopg2-binary==2.9.9
    pdfplumber==0.10.4
    playwright==1.41.0
    python-dotenv==1.0.0

Create scraper/.env with DATABASE_URL and OPENAI_API_KEY
Run playwright install chromium (for JS-rendered pages)
 2.2 — Fetcher module

Create scraper/fetcher.py:

fetch_page(url) function:

First attempt: requests.get() with realistic User-Agent header
Check response status code and content length
If 403 or empty content: fallback to Playwright headless browser
Return HTML string or None on failure


Playwright fallback:

Launch headless Chromium
Navigate to URL, wait for page load (networkidle)
Return page.content()
Close browser


Logging: Log URL, method used (requests vs playwright), status code, content length


Verify: python -c "from fetcher import fetch_page; print(len(fetch_page('https://www.longotoyota.com/new-vehicle-specials/')))" returns HTML


 2.3 — Extractor module

Create scraper/extractor.py:

extract_offers(html, dealer_name) function:

Clean HTML with BeautifulSoup: soup.get_text(separator='\n', strip=True)
Truncate to 15,000 characters
Send to GPT-4 with extraction prompt from CLAUDE.md
Parse JSON response
Strip markdown code fences if present (json ... )
Handle JSON parse errors gracefully (log and return empty list)
Return list of offer dicts


Use temperature=0 for consistent extraction
Use response_format={"type": "json_object"} if available, otherwise parse manually
Log: Number of offers extracted, any parse errors, token usage


Verify: Run on Longo Toyota HTML, confirm offers extracted look reasonable


 2.4 — Validator module

Create scraper/validators.py:

validate_offer(offer_dict) function:

Returns (is_valid: bool, errors: list[str])
Checks:

monthly_payment between $50 and $2,000
down_payment between $0 and $20,000 (or null)
term_months in [24, 27, 30, 33, 36, 39, 42, 48, 60, 72] (or null)
year is current year or next year
model is in TOYOTA_MODELS list
confidence >= 0.5
offer_type is "lease" or "finance"


Log validation failures with details


clean_offer(offer_dict) function:

Normalizes model names (case-insensitive match to TOYOTA_MODELS)
Converts string numbers to floats/ints
Sets defaults for missing optional fields




Verify: Valid offers pass, obviously bad data (negative prices, unknown models) fails


 2.5 — Saver module

Create scraper/saver.py:

save_offers(dealer_slug, offers) function:

Look up dealer by slug
Deactivate all existing active offers for this dealer: UPDATE offers SET active = FALSE WHERE dealer_id = X AND active = TRUE
Insert each new valid offer with active = TRUE
Store raw extracted data in raw_extracted_data JSONB field
Set extraction_method = "llm_html"
Set source_url to the dealer's specials_url
Log: offers deactivated count, offers inserted count




Verify: After running, database shows new offers for Longo Toyota, old seed data marked inactive


 2.6 — Main scraper entry point (single dealer)

Create scraper/main.py:

For now, just scrape Longo Toyota
Flow: fetch → extract → validate → save
Print summary: "Longo Toyota: Fetched OK, extracted 5 offers, 4 valid, saved 4"
Handle errors at every step without crashing


Verify: Run python main.py, check database has real offers from Longo Toyota



Phase 2 Checkpoint
bashcd scraper && python main.py
# Output like:
# Scraping Longo Toyota (https://www.longotoyota.com/new-vehicle-specials/)...
# Fetched 45,231 bytes via requests
# Extracted 5 offers via GPT-4
# Validated: 4 passed, 1 failed (monthly_payment was null)
# Saved 4 offers to database
# Done!

# Then verify via API:
curl http://localhost:8000/api/offers/search?model=RAV4
# → Should include real Longo Toyota offers

Phase 3: Scraper for All 5 Dealers
Goal: Scrape all 5 target dealers, handle failures gracefully, have 15+ real offers in database.
Tasks

 3.1 — Dealer configuration

Create scraper/config.py (or shared/dealer_list.py):

List of all 5 dealers with: name, slug, specials_url, city
Easy to add new dealers later


Update scraper/main.py to loop through all dealers


 3.2 — Error handling and resilience

Add try/except around each dealer's scrape cycle
If one dealer fails, log the error and continue to next
Add retry logic: if fetch fails, wait 5 seconds, try once more
Add rate limiting: sleep 3-5 seconds between dealers
Track results per dealer: success/failure/offers_count


 3.3 — Handle different site structures

Test fetcher on all 5 dealer URLs
Some may need Playwright (JS rendering)
Some may have different HTML structures
The LLM extraction prompt should handle this — but verify output quality for each
If a site requires special handling, add notes in dealer config


 3.4 — Scraper summary report

After scraping all dealers, print summary:



    Scraper Run Complete (2025-02-04 10:00:00)
    ──────────────────────────────────────────
    Longo Toyota:          ✓ 4 offers saved
    Toyota of Downtown LA: ✓ 3 offers saved
    Toyota Santa Monica:   ✓ 5 offers saved
    Keyes Toyota:          ✗ Failed (403 Forbidden)
    Toyota of Glendora:    ✓ 3 offers saved
    ──────────────────────────────────────────
    Total: 15 offers saved, 1 dealer failed

 3.5 — Verify data quality

Manually check 5 random offers against actual dealer websites
Confirm prices, terms, models match what's on the dealer site
Adjust extraction prompt if needed for accuracy
Fix any systematic extraction errors



Phase 3 Checkpoint
bashcd scraper && python main.py
# → All 5 dealers attempted, at least 3 succeed, 15+ total offers in database

curl http://localhost:8000/api/offers/search
# → Returns offers from multiple dealers

curl "http://localhost:8000/api/offers/search?max_monthly_payment=300"
# → Returns subset of cheaper offers

Phase 4: AI Chat Agent
Goal: User types natural language, GPT-4 parses it, calls search function, returns formatted response with real offers.
Tasks

 4.1 — AI agent service

Create backend/services/ai_agent.py:

System prompt from CLAUDE.md
Tool/function definition for search_offers
process_chat(message: str) function:

Call GPT-4 with user message + system prompt + tools
If GPT-4 calls search_offers function:

Parse function arguments
Execute search_offers_cached() with those params
Send results back to GPT-4 as tool response
Get GPT-4's formatted response


If no function call (user asked something general):

Return GPT-4's direct response


Return: response text + offers list + parsed search params


Log: user message, parsed params, offers count, response length, latency




 4.2 — Wire up chat endpoint

Update backend/api/chat.py:

POST /api/chat calls process_chat()
Returns ChatResponse with response text, offers, and search_params
Log search to search_logs table
Handle errors: if GPT-4 fails, return friendly error message




 4.3 — Test with real queries

Test these queries and verify correct behavior:



    "RAV4 lease under $350"              → Should return RAV4 offers under $350/mo
    "cheapest Toyota lease"              → Should return lowest payment offers
    "Camry deals"                        → Should return Camry-specific offers
    "what's available under $300/month"  → Should filter by $300 max payment
    "best deal right now"                → Should return all offers sorted by price
    "Honda Civic lease"                  → Should explain we only have Toyota in LA
    "what's the weather?"                → Should redirect to car deals
    "tell me about the RAV4"             → Should give general info + current offers

Fix any parsing issues or unexpected behavior
 4.4 — Caching integration

Ensure search results are cached (GPT-4 query parsing is NOT cached, results ARE cached)
Verify second identical search is faster (cache hit logged)



Phase 4 Checkpoint
bashcurl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "RAV4 lease under $350 in LA"}'
# → Returns AI response with real offers from database

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "cheapest Toyota lease available"}'
# → Returns lowest payment offers across all models

Phase 5: Frontend
Goal: Working Next.js app where user can search for deals and see results.
Tasks

 5.1 — Initialize frontend

Create Next.js 14 app with App Router:



bash    npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"

Install dependencies:

bash    cd frontend
    npx shadcn-ui@latest init
    npx shadcn-ui@latest add button card input badge skeleton
    npm install ai openai lucide-react

Set up .env.local with NEXT_PUBLIC_API_URL
Verify: npm run dev shows default Next.js page
 5.2 — TypeScript types

Create frontend/lib/types.ts:

Types matching backend Pydantic schemas: Offer, Dealer, ChatResponse, SearchParams


Create frontend/lib/api.ts:

searchOffers(params) → calls GET /api/offers/search
getOffer(id) → calls GET /api/offers/{id}
sendChat(message) → calls POST /api/chat
Error handling wrapper for all API calls




 5.3 — Layout and header

Update app/layout.tsx:

Clean layout with system font
Meta tags: title "CarDealsAI — Find Real Car Deals", description


Create components/Header.tsx:

Simple header: Logo "CarDealsAI" (text, no image) + tagline
Links: Home, About (future)
Clean, minimal




 5.4 — Homepage

Update app/page.tsx:

Hero section: "Find Real Car Deals" headline
Subtext: "Search current Toyota lease offers in LA. Every deal links to its source."
ChatInput component (large, prominent)
Example query chips below input (clickable, populate input)
"How it works" section (3 steps, simple icons from lucide-react)
"Currently tracking 5 Toyota dealers in Los Angeles" footer note




 5.5 — ChatInput component

Create components/ChatInput.tsx:

Large text input with submit button
Placeholder: "What car deal are you looking for?"
Submit on Enter or button click
Loading state: Input disabled, spinner shown
On submit: calls sendChat(), navigates to results or shows results inline




 5.6 — Chat/Results display

Create components/ChatMessages.tsx:

Displays AI response text
Below text, renders OfferCard for each offer in response
Loading state: Skeleton cards
Empty state: "No offers found" message with suggestions
Allow follow-up queries (input stays visible below results)




 5.7 — OfferCard component

Create components/OfferCard.tsx:

Card layout as specified in CLAUDE.md
Shows: year, model, trim, monthly payment, down payment, term, mileage, dealer name, city
Confidence indicator (color-coded dot or bar)
"Updated X ago" relative time
"View Source" button → opens source_url in new tab
"See Details" button → links to /offer/[id]
Responsive: full width on mobile, grid on desktop




 5.8 — Offer detail page

Create app/offer/[id]/page.tsx:

Fetches full offer data from GET /api/offers/{id}
Shows all offer details in clean layout
Dealer info section: name, address, phone, website link
Prominent source link: "This offer was found at [Dealer Name] →"
Disclaimer text (expandable/collapsible)
Back button to return to search
"Report an Issue" link (mailto: for V0)




 5.9 — Mobile responsive

Test all pages on mobile viewport (375px wide)
Offer cards: single column stack
Chat input: full width
Header: simplified
Touch-friendly buttons (min 44px tap targets)



Phase 5 Checkpoint
- Homepage loads with chat input
- Type "RAV4 lease under $350" → see AI response + offer cards
- Click "View Source" → opens dealer website
- Click "See Details" → see full offer page
- Works on mobile screen size

Phase 6: Connect + Polish
Goal: Everything works end-to-end, edge cases handled, ready for real users.
Tasks

 6.1 — End-to-end testing

Test 10 different queries end-to-end (browser → API → GPT-4 → database → response)
Test: What happens with no results?
Test: What happens if API is slow?
Test: What happens if GPT-4 fails?
Test: What happens with gibberish input?
Test: What happens with very long input?


 6.2 — Error handling (frontend)

API unreachable: Show "Service temporarily unavailable, please try again"
Slow response: Show loading state, timeout after 30 seconds
No results: Helpful message with suggestions
Invalid offer ID: 404 page


 6.3 — Error handling (backend)

GPT-4 API fails: Return cached results if available, otherwise friendly error
Database connection fails: Return 503 with appropriate message
Invalid search params: Return 422 with validation errors
Rate limiting: Basic rate limit on /api/chat (10 requests per minute per IP for V0)


 6.4 — Performance polish

Frontend: Loading skeletons for all data-dependent components
Backend: Verify caching is working (log cache hit/miss)
Database: Check query performance with EXPLAIN, ensure indexes are used
Overall: Chat response should be under 5 seconds for cached queries


 6.5 — Final UI polish

Consistent spacing and alignment
All links work
No console errors
Favicon (simple car emoji or "CD" text)
OpenGraph meta tags for social sharing



Phase 6 Checkpoint
- Ask a friend to use the site without explanation
- Can they figure out how to search?
- Do the results make sense?
- Can they find the source for each deal?
- Does it work on their phone?

Phase 7: Deploy
Goal: Live on the internet, accessible by URL.
Tasks

 7.1 — Deploy backend to Fly.io

Create backend/Dockerfile:



dockerfile    FROM python:3.11-slim
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY . .
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

Create backend/fly.toml config
Set secrets: fly secrets set OPENAI_API_KEY=... DATABASE_URL=...
Deploy: fly deploy
Verify: curl https://yourapp.fly.dev/api/health returns OK
 7.2 — Deploy frontend to Vercel

Connect GitHub repo to Vercel
Set environment variable: NEXT_PUBLIC_API_URL=https://yourapp.fly.dev
Deploy
Verify: Site loads at yourproject.vercel.app


 7.3 — Custom domain (optional for V0)

Buy domain (cardealsai.com or similar)
Point to Vercel
Update CORS on backend to include new domain


 7.4 — Set up daily scraper

Option A: GitHub Actions cron job



yaml    on:
      schedule:
        - cron: '0 10 * * *'  # 10am UTC daily

Option B: Fly.io scheduled machine
Verify: Scraper runs automatically, new data appears in database
 7.5 — Monitoring

Sentry configured on both frontend and backend
Set up basic uptime monitoring (UptimeRobot, free tier)
Daily manual check: View /api/health, verify offer counts



Phase 7 Checkpoint
- Visit your live URL → site loads
- Search for "RAV4 lease" → see real offers
- Check /api/health → shows current offer counts
- Wait 24 hours → scraper ran, offers refreshed

Post-Launch Priorities (After V0 Works)
These are NOT part of V0. Only start these after everything above is working and deployed.

Add more dealers (10-15 more Toyota dealers in LA)
User accounts (magic link login)
Save/favorite offers (requires auth)
Premium tier (Stripe integration, paywall)
Dealer portal (simple CRUD for dealers to manage offers)
SEO content (blog posts targeting car deal keywords)
Deal alerts (email notifications when better deals appear)
Honda brand (second brand, 10+ dealers)
Compare offers (side-by-side comparison view)
Map view (show dealers on a map)