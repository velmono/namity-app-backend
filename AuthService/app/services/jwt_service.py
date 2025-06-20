from datetime import datetime, timedelta, timezone
from jose import jwt
from jose.exceptions import JWTError
from app.config import settings

_PRIVATE_KEY = settings.PRIVATE_KEY
_PUBLIC_KEY = settings.PUBLIC_KEY

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "iss": settings.ISSUER,
        "sub": user_id,
        "aud": "namity_api",
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, _PRIVATE_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(user_id: str, jti: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "iss": settings.ISSUER,
        "sub": user_id,
        "aud": "namity_refresh",
        "jti": jti,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, _PRIVATE_KEY, algorithm=settings.ALGORITHM)

def create_id_token(user_id: str, extra_claims: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "iss": settings.ISSUER,
        "sub": user_id,
        "aud": "namity_client",
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, _PRIVATE_KEY, algorithm=settings.ALGORITHM)

def verify_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            _PUBLIC_KEY,
            algorithms=[settings.ALGORITHM],
            audience="namity_api",
            issuer=settings.ISSUER,
        )
    except JWTError as e:
        raise ValueError(f"Invalid access token: {e}")

def verify_refresh_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            _PUBLIC_KEY,
            algorithms=[settings.ALGORITHM],
            audience="namity_refresh",
            issuer=settings.ISSUER,
        )
    except JWTError as e:
        raise ValueError(f"Invalid refresh token: {e}")