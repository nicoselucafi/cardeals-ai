"""Supabase JWT verification and user dependencies."""

import logging
import uuid
from typing import Optional

import jwt
from jwt import PyJWKClient
from fastapi import Depends, Request
from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models import User

logger = logging.getLogger(__name__)
settings = get_settings()

# JWKS client — fetches and caches the public keys from Supabase
# Uses the Supabase project URL from frontend config
_jwks_url = "https://vlqltlmucoydgagqzjrz.supabase.co/auth/v1/.well-known/jwks.json"
_jwks_client = PyJWKClient(_jwks_url, cache_keys=True)


def verify_supabase_token(token: str) -> dict:
    """Decode and verify a Supabase JWT token.

    Supports both ES256 (newer Supabase projects) and HS256 (legacy).
    Returns the decoded payload with 'sub' (user UUID) and 'email'.
    Raises HTTPException 401 on invalid/expired tokens.
    """
    try:
        # Try JWKS-based verification first (ES256)
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            options={"verify_aud": False},
        )
        return payload
    except (jwt.exceptions.PyJWKClientError, jwt.InvalidTokenError) as jwks_err:
        logger.debug(f"JWKS verification failed: {jwks_err}, trying HS256 fallback")

    # Fallback to HS256 with shared secret
    if not settings.supabase_jwt_secret:
        logger.error("JWT verification failed and no SUPABASE_JWT_SECRET configured")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT (both ES256 and HS256 failed): {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: extract and verify Bearer token, return User.

    - Extracts Authorization: Bearer <token> header
    - Decodes JWT, gets sub (user UUID) and email
    - Get-or-create User row using the Supabase UUID as PK
    - Returns the User model instance
    - Raises 401 if no token or invalid token
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = auth_header.split(" ", 1)[1]
    payload = verify_supabase_token(token)

    user_id_str = payload.get("sub")
    email = payload.get("email")

    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

    user_uuid = uuid.UUID(user_id_str)

    # Get or create user
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()

    if not user:
        user = User(id=user_uuid, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Created new user: {email} ({user_uuid})")

    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """FastAPI dependency: same as get_current_user but returns None instead of 401.

    Use this for endpoints that work for both authenticated and anonymous users.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        token = auth_header.split(" ", 1)[1]
        payload = verify_supabase_token(token)
    except HTTPException:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    user_uuid = uuid.UUID(user_id_str)

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()

    if not user:
        email = payload.get("email")
        user = User(id=user_uuid, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Created new user: {email} ({user_uuid})")

    return user
