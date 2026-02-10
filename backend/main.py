import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from config import get_settings
from database import engine
from rate_limit import limiter
from api import health, offers, chat

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure logging level based on environment
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: verify database connection
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified.")
    logger.info(f"Supabase JWT secret configured: {bool(settings.supabase_jwt_secret)} (length: {len(settings.supabase_jwt_secret)})")
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="CarDealsAI API",
    description="AI-powered car deals search engine for Toyota dealers in Los Angeles",
    version="0.1.0",
    lifespan=lifespan,
    # Disable interactive docs in production
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

# Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handler — prevent internal details from leaking
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )


# API key middleware — protects endpoints in production
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Skip auth if no API key is configured (development mode)
    if not settings.api_secret_key:
        return await call_next(request)

    # Public endpoints that don't require auth
    public_paths = {"/", "/api/health", "/docs", "/redoc", "/openapi.json"}
    if request.url.path in public_paths:
        return await call_next(request)

    # Public API paths (offers browsing is open to all)
    if request.url.path.startswith("/api/offers"):
        return await call_next(request)

    # CORS preflight requests don't carry auth headers
    if request.method == "OPTIONS":
        return await call_next(request)

    # Allow requests with Bearer token (auth handled at endpoint level)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return await call_next(request)

    # Check API key header
    api_key = request.headers.get("X-API-Key")
    if api_key != settings.api_secret_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key"},
        )

    return await call_next(request)


# CORS - restrict to configured origins + Vercel preview URLs
cors_origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://cardeals-.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)
logger.info(f"CORS: Allowing origins {cors_origins} + Vercel preview URLs")

# Include routers
app.include_router(health.router)
app.include_router(offers.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "CarDealsAI API",
        "version": "0.1.0",
        "health": "/api/health",
    }
