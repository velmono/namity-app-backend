from fastapi import Depends, HTTPException, status, Cookie
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.config import settings
from app.database import session_dependency
from app.models import Profile
from app.services.profile_service import create_or_update_profile
from app.schemas import ProfileCreate

public_key = Path(settings.PUBLIC_KEY_PATH).read_text()

async def get_current_profile(
    db: session_dependency,
    access_token: str = Cookie(None, description="Access token cookie"),
) -> Profile:
    if not access_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing access token")
    try:
        payload = jwt.decode(
            access_token,
            public_key,
            algorithms=[settings.ALGORITHM],
            issuer=settings.ISSUER,
            audience=settings.AUDIENCE,
        )
    except JWTError as e:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            f"Invalid token: {e}"
        )
    user_id = payload.get("sub")
    profile = await db.get(Profile, user_id)
    if not profile:
        # Auto-create profile with default slug = user_id
        profile_data = ProfileCreate(
            slug=user_id,
            display_name=None,
            bio=None,
            avatar_url=None
        )
        profile = await create_or_update_profile(user_id, profile_data, db)
    return profile