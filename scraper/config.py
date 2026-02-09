"""Scraper configuration and dealer list."""

import os
from dotenv import load_dotenv

load_dotenv()

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROXY_URL = os.getenv("PROXY_URL", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Known Toyota models for validation
TOYOTA_MODELS = [
    "4Runner", "bZ4X", "Camry", "Corolla", "Corolla Cross",
    "Crown", "GR86", "GR Corolla", "GR Supra", "Grand Highlander",
    "Highlander", "Land Cruiser", "Mirai", "Prius", "RAV4",
    "Sequoia", "Sienna", "Tacoma", "Tundra", "Venza"
]

# Known Honda models for validation
HONDA_MODELS = [
    "Accord", "Accord Hybrid", "Civic", "Civic Hybrid", "Civic Hatchback",
    "CR-V", "CR-V Hybrid", "HR-V", "Passport", "Pilot",
    "Prologue", "Ridgeline", "Odyssey", "Insight"
]

# Known Tesla models for validation
TESLA_MODELS = [
    "Model 3", "Model Y", "Model S", "Model X", "Cybertruck"
]

# All supported models (combined)
ALL_MODELS = TOYOTA_MODELS + HONDA_MODELS + TESLA_MODELS

# ============================================================
# Target dealerships - verified working sources
# Grouped by platform for easier maintenance
# ============================================================
DEALERS = [
    # ============================================
    # Platform: Octane
    # ============================================
    {
        "name": "Longo Toyota",
        "slug": "longo-toyota",
        "make": "Toyota",
        "specials_url": "https://www.longotoyota.com/new-toyota-specials-los-angeles.html",
        "city": "El Monte",
        "platform": "octane",
    },

    # ============================================
    # Platform: DealerOn / Gemini
    # ============================================
    {
        "name": "Toyota of Downtown LA",
        "slug": "toyota-downtown-la",
        "make": "Toyota",
        "specials_url": "https://www.toyotaofdowntownla.com/new-vehicle-specials/",
        "city": "Los Angeles",
        "platform": "dealeron_gemini",
    },
    {
        "name": "North Hollywood Toyota",
        "slug": "north-hollywood-toyota",
        "make": "Toyota",
        "specials_url": "https://www.northhollywoodtoyota.com/new-vehicle-specials/",
        "city": "North Hollywood",
        "platform": "dealeron_gemini",
    },

    # ============================================
    # Platform: DealerInspire
    # ============================================
    {
        "name": "Culver City Toyota",
        "slug": "culver-city-toyota",
        "make": "Toyota",
        "specials_url": "https://www.culvercitytoyota.com/new-vehicles/new-vehicle-specials/",
        "city": "Culver City",
        "platform": "dealerinspire",
    },
    {
        "name": "AutoNation Toyota Cerritos",
        "slug": "autonation-toyota-cerritos",
        "make": "Toyota",
        "specials_url": "https://www.autonationtoyotacerritos.com/toyota-specials.htm",
        "city": "Cerritos",
        "platform": "dealerinspire",
    },
    {
        "name": "Airport Marina Honda",
        "slug": "airport-marina-honda",
        "make": "Honda",
        "specials_url": "https://www.airportmarinahonda.com/new-vehicle-specials-2/",
        "city": "Los Angeles",
        "platform": "dealerinspire",
    },
    {
        "name": "Galpin Honda",
        "slug": "galpin-honda",
        "make": "Honda",
        "specials_url": "https://www.galpinhonda.com/new-specials/",
        "city": "Mission Hills",
        "platform": "dealerinspire",
    },
    {
        "name": "Goudy Honda",
        "slug": "goudy-honda",
        "make": "Honda",
        "specials_url": "https://www.goudyhonda.com/new-vehicles/new-vehicle-specials/",
        "city": "Alhambra",
        "platform": "dealerinspire",
    },
    {
        "name": "Norm Reeves Honda Cerritos",
        "slug": "norm-reeves-honda-cerritos",
        "make": "Honda",
        "specials_url": "https://www.normreeveshondacerritos.com/new-vehicles/new-vehicle-specials/",
        "city": "Cerritos",
        "platform": "dealerinspire",
    },

    # ============================================
    # No CSS extractor - uses LLM fallback
    # ============================================
    {
        "name": "Scott Robinson Honda",
        "slug": "scott-robinson-honda",
        "make": "Honda",
        "specials_url": "https://scottrobinsonhonda.com/offers/",
        "city": "Torrance",
        "platform": "unknown",
    },
    {
        "name": "Carson Honda",
        "slug": "carson-honda",
        "make": "Honda",
        "specials_url": "https://www.carsonhonda.net/promotions/new/index.htm",
        "city": "Carson",
        "platform": "dealer_com",
    },
]

# Minimum indicators required in page text before calling GPT
# This prevents wasting tokens on pages without real offers
OFFER_KEYWORDS = [
    "/mo", "/month", "per month", "monthly",
    "lease", "finance", "apr", "due at signing",
    "$2", "$3", "$4", "$5",  # Price indicators
]
MIN_OFFER_KEYWORDS = 3  # Must have at least this many to proceed with extraction

# Request settings
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Rate limiting
DELAY_BETWEEN_DEALERS = 2  # seconds between dealers
