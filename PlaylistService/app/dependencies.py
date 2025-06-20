from fastapi import Depends, HTTPException, Cookie
from jose import jwt, JWTError
from pathlib import Path
from app.config import settings

_PUBLIC_KEY = Path(settings.PUBLIC_KEY_PATH).read_text()

async def get_current_user_id(
    access_token: str = Cookie(None),
) -> str:
    if not access_token:
        raise HTTPException(401, "Missing access token")
    try:
        payload = jwt.decode(
            access_token,
            _PUBLIC_KEY,
            algorithms=[settings.ALGORITHM],
            issuer=settings.ISSUER,
            audience=settings.AUDIENCE,
        )
    except JWTError as e:
        raise HTTPException(401, f"Invalid token: {e}")
    return payload["sub"] 