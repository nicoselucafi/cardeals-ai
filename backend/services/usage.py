"""Usage tracking service for free tier chat limits."""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import ChatUsage, User

logger = logging.getLogger(__name__)

FREE_CHAT_LIMIT = 10
FREE_COMPARE_LIMIT = 10

# Keep for backward compat with imports
FREE_DAILY_LIMIT = FREE_CHAT_LIMIT


def _get_limit_for_source(source: str) -> int:
    if source == "compare":
        return FREE_COMPARE_LIMIT
    return FREE_CHAT_LIMIT


async def get_daily_chat_usage(db: AsyncSession, user_id, source: str = "chat") -> int:
    """Count how many chat prompts the user has used today (UTC) for a given source."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    result = await db.execute(
        select(func.count(ChatUsage.id)).where(
            ChatUsage.user_id == user_id,
            ChatUsage.source == source,
            ChatUsage.used_at >= today_start,
        )
    )
    return result.scalar() or 0


async def record_chat_usage(db: AsyncSession, user_id, source: str = "chat") -> None:
    """Record one chat prompt usage for the user."""
    usage = ChatUsage(user_id=user_id, source=source)
    db.add(usage)
    await db.commit()


async def check_chat_allowed(
    db: AsyncSession, user: User, source: str = "chat"
) -> tuple[bool, int, int]:
    """Check if the user is allowed to send a chat prompt.

    Returns (allowed, used, limit).
    Premium users: limit = -1 (unlimited).
    Free users: limit depends on source.
    """
    if user.is_premium:
        used = await get_daily_chat_usage(db, user.id, source)
        return True, used, -1

    limit = _get_limit_for_source(source)
    used = await get_daily_chat_usage(db, user.id, source)
    allowed = used < limit
    return allowed, used, limit
