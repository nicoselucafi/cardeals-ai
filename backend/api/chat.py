"""Chat endpoint for natural language car deal searches."""

import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import User
from rate_limit import limiter
from schemas import ChatRequest, ChatResponse, ChatUsageResponse
from services.ai_agent import process_chat
from services.offer_search import log_search
from services.usage import check_chat_allowed, get_daily_chat_usage, record_chat_usage, _get_limit_for_source

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Chat endpoint for natural language car deal searches.

    Requires authentication. Free users get 10 prompts/day per source.
    Premium users have unlimited access.
    """
    source = body.source or "chat"
    logger.info(f"Chat request [{source}] from {current_user.email}: {body.message[:100]}...")

    # Check usage limits (tracked per source)
    allowed, used, limit = await check_chat_allowed(db, current_user, source)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Daily chat limit reached",
                "used": used,
                "limit": limit,
                "remaining": 0,
                "is_premium": current_user.is_premium,
            },
        )

    # Process chat with AI agent (pass conversation history for context)
    history = [{"role": m.role, "content": m.content} for m in body.history] if body.history else None
    response_text, offers, search_params = await process_chat(db, body.message, history=history)

    # Record usage with source
    await record_chat_usage(db, current_user.id, source)

    # Log the search
    await log_search(
        db=db,
        raw_query=body.message,
        parsed_params=search_params,
        results_count=len(offers),
        cached=False,
        user_id=current_user.id,
    )

    # Calculate remaining prompts
    remaining = None
    if limit > 0:
        remaining = max(0, limit - used - 1)

    return ChatResponse(
        response=response_text,
        offers=offers,
        search_params=search_params,
        remaining_prompts=remaining,
        daily_limit=limit,
        is_premium=current_user.is_premium,
    )


@router.get("/chat/usage", response_model=ChatUsageResponse)
async def chat_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    source: str = Query("chat", description="Source: 'chat' or 'compare'"),
) -> ChatUsageResponse:
    """Get current chat usage for the authenticated user without consuming a prompt."""
    used = await get_daily_chat_usage(db, current_user.id, source)
    limit = -1 if current_user.is_premium else _get_limit_for_source(source)
    remaining = -1 if current_user.is_premium else max(0, limit - used)

    return ChatUsageResponse(
        used=used,
        limit=limit,
        remaining=remaining,
        is_premium=current_user.is_premium,
    )
