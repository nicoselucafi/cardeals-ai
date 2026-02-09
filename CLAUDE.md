# Car Deals AI Agent — CLAUDE.md

You are building an AI-powered car deals search engine called **CarDealsAI**.  
Users type natural language queries like "best RAV4 lease in LA under $350/month" and get real, current dealer offers with proof links.

---

## Project Overview

- **What it does:** Scrapes Toyota dealer websites in Los Angeles, extracts lease/finance offers using GPT-4, stores them in a database, and lets users search via a chat interface.
- **Who it's for:** Car shoppers in LA looking for the best current deals.
- **Scope for V0:** 5 Toyota dealerships in LA. Toyota only. Lease offers only. No payments, no auth, no premium tier yet. Just a working end-to-end demo.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 14 (App Router) | Fast to build, great DX |
| UI Components | shadcn/ui + Tailwind CSS | Copy-paste components, consistent design |
| Chat Streaming | Vercel AI SDK (`ai` package) | Built-in streaming + function calling support |
| Frontend Hosting | Vercel | One-click deploy, free tier |
| Backend | Python 3.11+ with FastAPI | Fast to build, auto-generates API docs |
| Database | PostgreSQL on Supabase | Free tier, managed, easy setup |
| ORM | SQLAlchemy 2.0+ with asyncpg | Async support, mature ecosystem |
| AI | OpenAI GPT-4 Turbo (`gpt-4-turbo-preview`) | Best function calling, reliable extraction |
| Scraping | `requests` + `BeautifulSoup4` | Simple, sufficient for static pages |
| Scraping (JS sites) | `playwright` | Fallback for JavaScript-rendered dealer pages |
| PDF Extraction | `pdfplumber` | Handles dealer PDF specials |
| Object Storage | Backblaze B2 (S3-compatible) | Cheap, stores scraped PDFs and screenshots |
| Caching | `cachetools` (in-memory) for V0, Redis later | Keep it simple, upgrade when needed |
| Error Tracking | Sentry | Free tier, catches crashes |
| Analytics | Plausible | Privacy-friendly, $9/month |

---

## Project Structure

```
cardeals-ai/
├── CLAUDE.md                  # This file (you read this)
├── PLAN.md                    # Build phases and task tracking
├── README.md                  # Project readme
│
├── frontend/                  # Next.js 14 app
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── .env.local             # NEXT_PUBLIC_API_URL=http://localhost:8000
│   ├── app/
│   │   ├── layout.tsx         # Root layout with fonts, metadata
│   │   ├── page.tsx           # Homepage — hero + chat input
│   │   ├── globals.css        # Tailwind base styles
│   │   ├── search/
│   │   │   └── page.tsx       # Search results page (offer cards)
│   │   └── offer/
│   │       └── [id]/
│   │           └── page.tsx   # Individual offer detail page
│   ├── components/
│   │   ├── ui/                # shadcn/ui components (button, card, input, etc.)
│   │   ├── ChatInput.tsx      # Main search/chat input component
│   │   ├── ChatMessages.tsx   # Displays AI responses + offer cards
│   │   ├── OfferCard.tsx      # Single offer card (payment, dealer, term, source link)
│   │   ├── OfferDetail.tsx    # Full offer detail view
│   │   └── Header.tsx         # Simple site header/nav
│   └── lib/
│       ├── api.ts             # API client functions (fetch wrapper)
│       └── types.ts           # TypeScript types matching backend schemas
│
├── backend/                   # FastAPI app
│   ├── requirements.txt
│   ├── .env                   # DATABASE_URL, OPENAI_API_KEY, etc.
│   ├── main.py                # FastAPI app entry point, CORS, routers
│   ├── config.py              # Environment variable loading
│   ├── database.py            # SQLAlchemy engine, session, Base
│   ├── models.py              # SQLAlchemy ORM models (Dealer, Offer, User)
│   ├── schemas.py             # Pydantic schemas for API request/response
│   ├── api/
│   │   ├── chat.py            # POST /api/chat — AI agent with function calling
│   │   ├── offers.py          # GET /api/offers/search, GET /api/offers/{id}
│   │   └── health.py          # GET /api/health — basic health check
│   ├── services/
│   │   ├── ai_agent.py        # GPT-4 function calling logic, system prompt
│   │   ├── offer_search.py    # Database search queries with filters
│   │   └── cache.py           # In-memory caching layer (cachetools TTLCache)
│   └── seed.py                # Seed script: inserts 5 LA Toyota dealers + sample offers
│
├── scraper/                   # Standalone Python scraper
│   ├── requirements.txt
│   ├── .env                   # OPENAI_API_KEY, DATABASE_URL, PROXY_URL (optional for V0)
│   ├── main.py                # Entry point: loops through dealers, scrapes, extracts, saves
│   ├── config.py              # Dealer list with URLs and metadata
│   ├── fetcher.py             # Fetch HTML (requests + optional playwright fallback)
│   ├── extractor.py           # GPT-4 LLM extraction: HTML/text → structured JSON offers
│   ├── pdf_extractor.py       # Extract offers from dealer PDF specials
│   ├── saver.py               # Save extracted offers to database
│   └── validators.py          # Validate extracted data (price ranges, required fields)
│
└── shared/                    # Shared config (optional)
    └── dealer_list.py         # Master list of dealers and their specials URLs
```

---

## V0 Target Dealerships (5 Toyota Dealers in LA)

Use these specific dealerships. They are real, have public specials pages, and represent different website platforms:

| # | Dealership | City | Specials URL | Notes |
|---|-----------|------|-------------|-------|
| 1 | Longo Toyota | El Monte | `https://www.longotoyota.com/new-vehicle-specials/` | Largest Toyota dealer in US |
| 2 | Toyota of Downtown LA | Los Angeles | `https://www.toyotaofdowntownla.com/new-vehicle-specials/` | DealerOn platform |
| 3 | Toyota Santa Monica | Santa Monica | `https://www.santamonicatoyota.com/new-vehicle-specials/` | Coastal LA |
| 4 | Keyes Toyota | Van Nuys | `https://www.keystoyota.com/new-vehicle-specials/` | San Fernando Valley |
| 5 | Toyota of Glendora | Glendora | `https://www.toyotaofglendora.com/new-vehicle-specials/` | East LA |

**Important:** These URLs may change. If a URL returns a 404 or redirect during scraping, log it and skip — don't crash the whole scraper.

---

## Database Schema

Use these exact tables. Do not add extra tables for V0.

```sql
-- Dealers table
CREATE TABLE dealers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,        -- URL-friendly name: "longo-toyota"
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2) DEFAULT 'CA',
    zip VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    website VARCHAR(500),
    specials_url VARCHAR(500) NOT NULL,        -- The page we scrape
    phone VARCHAR(20),
    platform VARCHAR(100),                     -- "DealerOn", "Dealer.com", "custom", etc.
    verified BOOLEAN DEFAULT FALSE,            -- For future paid dealer tier
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Offers table (the core data)
CREATE TABLE offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dealer_id UUID NOT NULL REFERENCES dealers(id) ON DELETE CASCADE,

    -- Vehicle info
    year INT NOT NULL,
    make VARCHAR(50) NOT NULL DEFAULT 'Toyota',
    model VARCHAR(100) NOT NULL,               -- "RAV4", "Camry", "Corolla", etc.
    trim VARCHAR(100),                         -- "LE", "XLE", "SE", etc.

    -- Offer details
    offer_type VARCHAR(20) NOT NULL DEFAULT 'lease',  -- "lease" or "finance"
    monthly_payment DECIMAL(10, 2),            -- Dollars, e.g. 299.00
    down_payment DECIMAL(10, 2),               -- Due at signing, e.g. 3500.00
    term_months INT,                           -- 24, 36, 48
    annual_mileage INT,                        -- 10000, 12000, 15000
    apr DECIMAL(5, 2),                         -- For finance offers
    msrp DECIMAL(10, 2),                       -- Sticker price if available
    selling_price DECIMAL(10, 2),              -- Discounted price if available

    -- Offer validity
    offer_start_date DATE,
    offer_end_date DATE,
    disclaimer TEXT,                            -- Fine print from dealer

    -- Source tracking (proof)
    source_url VARCHAR(500),                   -- URL where we found this offer
    source_pdf_url VARCHAR(500),               -- If extracted from a PDF
    screenshot_url VARCHAR(500),               -- Screenshot of the offer page (future)

    -- Quality tracking
    confidence_score DECIMAL(3, 2) DEFAULT 0.80, -- 0.00 to 1.00, set by extractor
    extraction_method VARCHAR(50),              -- "llm_html", "llm_pdf", "manual"
    raw_extracted_data JSONB,                  -- Full LLM response for debugging

    -- Status
    active BOOLEAN DEFAULT TRUE,
    verified_by_human BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table (minimal for V0, expand later for premium)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search log (track what users search for — useful for analytics)
CREATE TABLE search_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_query TEXT NOT NULL,                    -- What the user typed
    parsed_params JSONB,                       -- What GPT-4 extracted: {make, model, max_payment...}
    results_count INT,
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for search performance
CREATE INDEX idx_offers_active ON offers(active) WHERE active = TRUE;
CREATE INDEX idx_offers_make_model ON offers(make, model) WHERE active = TRUE;
CREATE INDEX idx_offers_payment ON offers(monthly_payment) WHERE active = TRUE;
CREATE INDEX idx_offers_dealer ON offers(dealer_id) WHERE active = TRUE;
CREATE INDEX idx_offers_type ON offers(offer_type) WHERE active = TRUE;
CREATE INDEX idx_dealers_active ON dealers(active) WHERE active = TRUE;
CREATE INDEX idx_search_logs_created ON search_logs(created_at);
```

---

## AI Agent Specification

### System Prompt

```
You are CarDealsAI, a helpful assistant that finds real car lease and finance deals from Toyota dealerships in Los Angeles.

When a user asks about car deals:
1. Extract their preferences: make, model, budget (max monthly payment), offer type (lease/finance)
2. Call the search_offers function with these parameters
3. Present the top results clearly with:
   - Monthly payment and terms
   - Down payment / due at signing
   - Dealer name and city
   - How fresh the offer is
   - A brief explanation of why this deal is good or notable

If the user asks follow-up questions about specific offers, answer using the offer data.
If the user asks something unrelated to car deals, politely redirect them.

Keep responses concise (under 200 words). Be friendly, direct, and helpful.
Never make up offers. Only present data from the search_offers function.
If no offers match, say so honestly and suggest broadening their search.

Current coverage: Toyota dealers in Los Angeles area only.
```

### Function Calling Tool Definition

```json
{
  "type": "function",
  "function": {
    "name": "search_offers",
    "description": "Search for current vehicle lease and finance offers from Toyota dealerships in Los Angeles. Returns matching offers sorted by best value.",
    "parameters": {
      "type": "object",
      "properties": {
        "model": {
          "type": "string",
          "description": "Toyota model name, e.g. 'RAV4', 'Camry', 'Corolla', 'Highlander', 'Tacoma', '4Runner', 'Prius', 'Sienna'. Optional — omit to search all models."
        },
        "max_monthly_payment": {
          "type": "number",
          "description": "Maximum monthly payment in dollars. e.g. 350 means '$350/month or less'. Optional."
        },
        "offer_type": {
          "type": "string",
          "enum": ["lease", "finance"],
          "description": "Type of offer. Defaults to 'lease' if not specified."
        },
        "max_down_payment": {
          "type": "number",
          "description": "Maximum down payment / due at signing in dollars. Optional."
        },
        "min_term_months": {
          "type": "integer",
          "description": "Minimum lease/finance term in months. Optional."
        },
        "max_term_months": {
          "type": "integer",
          "description": "Maximum lease/finance term in months. Optional."
        }
      },
      "required": []
    }
  }
}
```

### Search Logic (offer_search.py)

The `search_offers` function should:
1. Check in-memory cache first (keyed on sorted parameter tuple, 1-hour TTL)
2. If cache miss, query PostgreSQL with filters
3. Sort results by: `monthly_payment ASC, confidence_score DESC`
4. Return top 5 results (V0 shows all 5, no paywall yet)
5. Cache the results
6. Log the search to `search_logs` table

---

## Scraper Specification

### Extraction Prompt

Use this prompt template for GPT-4 to extract offers from dealer page HTML:

```
Extract all current vehicle lease and finance offers from this Toyota dealership page.

Return a JSON array. Each offer should have this structure:
{
  "year": 2025,
  "make": "Toyota",
  "model": "RAV4",
  "trim": "LE",
  "offer_type": "lease",
  "monthly_payment": 299.00,
  "down_payment": 3499.00,
  "term_months": 36,
  "annual_mileage": 12000,
  "apr": null,
  "msrp": null,
  "selling_price": null,
  "offer_end_date": "2025-02-28",
  "disclaimer": "Plus tax, title, license. On approved credit...",
  "confidence": 0.95
}

Rules:
- Only extract CURRENT offers (not expired)
- Use null for any field you cannot determine
- monthly_payment and down_payment are in dollars (not cents)
- Set confidence between 0.0 and 1.0:
  - 0.9+ : All key fields clearly stated
  - 0.7-0.9 : Most fields clear, some inferred
  - 0.5-0.7 : Several fields uncertain or missing
  - Below 0.5 : Don't include the offer
- If no valid offers found, return an empty array []
- Return ONLY the JSON array, no explanation or markdown

Dealership page content:
{page_text}
```

### Scraper Flow

```
1. For each dealer in dealer_list:
   a. Fetch specials page HTML (requests, with User-Agent header)
   b. If fetch fails (403, timeout, etc.):
      - Try with playwright (headless Chrome) as fallback
      - If still fails, log error and skip this dealer
   c. Clean HTML → extract text with BeautifulSoup (get_text with separator='\n')
   d. Truncate to 15,000 characters (GPT-4 context management)
   e. Send to GPT-4 with extraction prompt
   f. Parse JSON response
   g. Validate each offer (validators.py):
      - monthly_payment must be between $50 and $2000
      - down_payment must be between $0 and $20000
      - term_months must be in [24, 27, 30, 33, 36, 39, 42, 48, 60, 72]
      - year must be current year or next year
      - model must be a known Toyota model
      - confidence must be >= 0.5
   h. Deactivate old offers for this dealer (SET active = FALSE)
   i. Insert new offers with active = TRUE
   j. Log results: dealer name, offers found, offers saved, errors
   k. Sleep 3-5 seconds between dealers (rate limiting)
```

### Known Toyota Models (for validation)

```python
TOYOTA_MODELS = [
    "4Runner", "bZ4X", "Camry", "Corolla", "Corolla Cross",
    "Crown", "GR86", "GR Corolla", "GR Supra", "Grand Highlander",
    "Highlander", "Land Cruiser", "Mirai", "Prius", "RAV4",
    "Sequoia", "Sienna", "Tacoma", "Tundra", "Venza"
]
```

---

## API Endpoints

### POST /api/chat

**Request:**
```json
{
  "message": "best RAV4 lease under $350 in LA",
  "conversation_id": "optional-uuid"
}
```

**Response (streamed):**
```json
{
  "response": "I found 4 RAV4 lease offers under $350/month...",
  "offers": [
    {
      "id": "uuid",
      "dealer_name": "Longo Toyota",
      "dealer_city": "El Monte",
      "year": 2025,
      "model": "RAV4",
      "trim": "LE",
      "monthly_payment": 299.00,
      "down_payment": 3499.00,
      "term_months": 36,
      "annual_mileage": 12000,
      "offer_type": "lease",
      "source_url": "https://www.longotoyota.com/new-vehicle-specials/",
      "confidence_score": 0.92,
      "last_updated": "2025-02-03T10:00:00Z"
    }
  ],
  "search_params": {
    "model": "RAV4",
    "max_monthly_payment": 350,
    "offer_type": "lease"
  }
}
```

### GET /api/offers/search

**Query Parameters:**
- `model` (string, optional)
- `max_monthly_payment` (float, optional)
- `offer_type` (string, optional, default: "lease")
- `max_down_payment` (float, optional)
- `limit` (int, optional, default: 10, max: 50)
- `sort_by` (string, optional, default: "monthly_payment", options: "monthly_payment", "confidence_score", "down_payment")

**Response:**
```json
{
  "offers": [...],
  "total": 12,
  "filters_applied": {...}
}
```

### GET /api/offers/{id}

Returns full offer detail including raw_extracted_data and all fields.

### GET /api/health

Returns `{"status": "ok", "offers_count": 42, "dealers_count": 5, "last_scrape": "2025-02-03T10:00:00Z"}`

---

## Frontend Specification

### Homepage (app/page.tsx)

- Clean, minimal design
- Centered layout with:
  - Logo/title: "CarDealsAI" with tagline "Find real car deals with proof"
  - Large text input: Placeholder "What car deal are you looking for?"
  - Example queries below input as clickable chips:
    - "RAV4 lease under $350/mo"
    - "Cheapest Toyota lease in LA"
    - "Camry deals under $400/mo"
    - "Best Corolla lease"
  - Brief "How it works" section:
    1. We scrape dealer websites daily
    2. AI extracts current offers
    3. You search in plain English
    4. Every result links to the source

### Search Results (components/ChatMessages.tsx)

After user submits query:
- Show loading state: "Searching 5 Toyota dealers in LA..."
- Display AI response text (streamed)
- Below response, show OfferCard components for each result
- If no results: "No offers matched your search. Try broadening your criteria."

### Offer Card (components/OfferCard.tsx)

Each card shows:
```
┌─────────────────────────────────────────────┐
│  2025 Toyota RAV4 LE                        │
│  Longo Toyota · El Monte                    │
│                                              │
│  $299/mo  ·  36 months  ·  12K miles/yr     │
│  $3,499 due at signing                      │
│                                              │
│  Confidence: ●●●●○ (92%)                    │
│  Updated: 2 hours ago                       │
│                                              │
│  [View Source ↗]        [See Details →]      │
└─────────────────────────────────────────────┘
```

- "View Source" opens the dealer's specials page in new tab
- "See Details" navigates to /offer/[id]
- Confidence shown as dots or a simple bar (green > 85%, yellow 70-85%, red < 70%)
- "Updated X ago" shows time since last_verified/updated_at

### Offer Detail Page (app/offer/[id]/page.tsx)

Full offer details:
- All fields from the offer
- Dealer info (name, address, phone, website link)
- Source link prominently displayed: "This offer was found on [Dealer Website] →"
- Disclaimer text
- "Report Issue" button (emails you, or saves to a simple reports table)

### Design Guidelines

- Use shadcn/ui components: Card, Button, Input, Badge, Skeleton (loading)
- Color palette: Clean whites/grays, blue accent for CTAs, green for good deals
- Typography: System font stack (Inter if you want to be specific)
- Responsive: Must work on mobile (cards stack vertically)
- No dark mode for V0 (keep it simple)

---

## Caching Implementation

### Strategy

```python
from cachetools import TTLCache

# Cache search results: keyed on sorted parameters, 1 hour TTL
search_cache = TTLCache(maxsize=500, ttl=3600)

def get_cache_key(**params):
    """Generate consistent cache key from search parameters."""
    sorted_params = sorted(params.items())
    return str(sorted_params)

def search_offers_cached(**params):
    key = get_cache_key(**params)
    if key in search_cache:
        return search_cache[key]
    results = search_offers_db(**params)
    search_cache[key] = results
    return results

def invalidate_all_caches():
    """Call this after scraper runs."""
    search_cache.clear()
```

### Cache Invalidation

- Clear ALL search caches after each scraper run
- TTL of 1 hour means stale data is bounded even if scraper doesn't trigger invalidation
- Log cache hit/miss ratio to monitor effectiveness

---

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/cardeals
OPENAI_API_KEY=sk-...
CORS_ORIGINS=http://localhost:3000,https://cardealsai.vercel.app
SENTRY_DSN=https://...@sentry.io/...
ENVIRONMENT=development
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Scraper (.env)
```
DATABASE_URL=postgresql://user:password@host:5432/cardeals
OPENAI_API_KEY=sk-...
PROXY_URL=                  # Empty for V0, add Bright Data later
LOG_LEVEL=INFO
```

---

## Rules and Conventions

1. **Keep it simple.** No premature optimization. No over-engineering. If in doubt, do the simpler thing.
2. **No Celery, no Redis, no message queues for V0.** Use `cachetools` for in-memory caching. Use simple cron/scheduled task for scraping.
3. **Toyota only, LA only for V0.** Do not build abstractions for multi-brand or multi-city yet.
4. **Every offer must have a source link.** This is the core trust feature. If we can't link to where we found it, don't show it.
5. **Log everything.** Every scraper run, every extraction, every search query. We need this data.
6. **Fail gracefully.** If one dealer's scraper fails, skip it and continue. Never crash the whole pipeline.
7. **Validate aggressively.** Don't trust LLM output blindly. Validate price ranges, required fields, model names.
8. **Mobile-first.** Design the frontend for mobile, then ensure it looks good on desktop.
9. **Type safety.** Use TypeScript for frontend, Pydantic schemas for backend.
10. **Git commits after each working phase.** Never go more than a few hours without committing working code.