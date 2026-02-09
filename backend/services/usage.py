"""Usage tracking service for free tier chat limits."""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import ChatUsage, User

logger = logging.getLogger(__name__)

FREE_DAILY_LIMIT = 5


async def get_daily_chat_usage(db: AsyncSession, user_id) -> int:
    """Count how many chat prompts the user has used today (UTC)."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    result = await db.execute(
        select(func.count(ChatUsage.id)).where(
            ChatUsage.user_id == user_id,
            ChatUsage.used_at >= today_start,
        )
    )
    return result.scalar() or 0


async def record_chat_usage(db: AsyncSession, user_id) -> None:
    """Record one chat prompt usage for the user."""
    usage = ChatUsage(user_id=user_id)
    db.add(usage)
    await db.commit()


async def check_chat_allowed(
    db: AsyncSession, user: User
) -> tuple[bool, int, int]:
    """Check if the user is allowed to send a chat prompt.

    Returns (allowed, used, limit).
    Premium users: limit = -1 (unlimited).
    Free users: limit = FREE_DAILY_LIMIT.
    """
    if user.is_premium:
        used = await get_daily_chat_usage(db, user.id)
        return True, used, -1

    used = await get_daily_chat_usage(db, user.id)
    allowed = used < FREE_DAILY_LIMIT
    return allowed, used, FREE_DAILY_LIMIT
