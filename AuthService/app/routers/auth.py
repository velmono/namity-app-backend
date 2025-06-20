from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user
from app.services.auth_service import (
    register_user_service,
    authenticate_user_service,
    refresh_tokens_service,
    change_password_service
)
from app.schemas import (
    UserCreate,
    UserRead,
    TokenRequest,
    RefreshRequest
)
from app.database import session_dependency
from app.config import settings
from app.schemas import ChangePassword


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
async def register(
    
    user_in: UserCreate,
    db: session_dependency,
):
    """
    Register a new user with email and password.
    """
    return await register_user_service(user_in, db)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    response: Response,
    form_data: TokenRequest,
    db: session_dependency,
):
    """
    Authenticate user and set auth cookies.
    """
    tokens = await authenticate_user_service(form_data, db)

    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return {"detail": "Logged in"}


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    response: Response,
    db: session_dependency,
    refresh_token: str = Cookie(None, description="Refresh token cookie"),
):
    """
    Refresh auth tokens and update auth cookies.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token cookie",
        )
    tokens = await refresh_tokens_service(
        RefreshRequest(refresh_token=refresh_token),
        db
    )
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return {"detail": "Tokens refreshed"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: session_dependency,
    refresh_token: str = Cookie(None, description="Refresh token cookie"),
):
    """
    Logout user by revoking refresh token and clearing cookies.
    """
    if refresh_token:
        await refresh_tokens_service(RefreshRequest(refresh_token=refresh_token), db)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "Logged out"}


@router.post(
    "/password/change",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_password(
    data: ChangePassword,
    db: session_dependency,
    current_user = Depends(get_current_user),
):
    """
    Change the password of the current user.
    """
    await change_password_service(current_user, data, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)