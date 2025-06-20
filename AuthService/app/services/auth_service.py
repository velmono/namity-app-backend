from datetime import datetime, timedelta, timezone
import bcrypt
import ulid
from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.schemas import (
    UserCreate, UserRead,
    TokenRequest, RefreshRequest,
    TokenResponse, ChangePassword
)
from app.services.jwt_service import (
    create_access_token, create_refresh_token,
    create_id_token, verify_refresh_token
)
from app.config import settings


async def register_user_service(
    user: UserCreate,
    db: AsyncSession
) -> UserRead:
    """
    Регистрирует нового пользователя
    """
    result = await db.execute(
        select(models.User).filter_by(email=user.email)
    )
    
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    hashed_password = bcrypt.hashpw(
        user.password.encode('utf-8'), bcrypt.gensalt()
    ).decode('utf-8')

    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserRead.model_validate(db_user)


async def _create_tokens(
    user: models.User,
    db: AsyncSession,
    scopes: list[str] | None = None
) -> TokenResponse:
    """
    Вспомогательная функция: создаёт запись RefreshToken
    и выдаёт TokenResponse.
    """
    # Генерируем JTI и сохраняем в БД
    jti = ulid.new().str
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    token_record = models.RefreshToken(
        user_id=user.id,
        jti=jti,
        expires_at=expires_at
    )
    db.add(token_record)
    await db.commit()

    # Создаём JWT
    access_tk = create_access_token(user.id)
    refresh_tk = create_refresh_token(user.id, jti)
    id_tk: str | None = None
    if scopes and "openid" in scopes:
        id_tk = create_id_token(user.id, {"email": user.email})

    return TokenResponse(
        access_token=access_tk,
        refresh_token=refresh_tk,
        id_token=id_tk
    )


async def authenticate_user_service(
    credentials: TokenRequest,
    db: AsyncSession
) -> TokenResponse:
    """
    Аутентифицирует пользователя по email и паролю.
    """
    result = await db.execute(
        select(models.User).filter_by(email=credentials.email)
    )
    user = result.scalars().first()
    if not user or not bcrypt.checkpw(
        credentials.password.encode('utf-8'),
        user.hashed_password.encode('utf-8')
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    return await _create_tokens(user, db, scopes=credentials.scope)


async def refresh_tokens_service(
    refresh_req: RefreshRequest,
    db: AsyncSession
) -> TokenResponse:
    """
    Обновляет токены: проверяет подпись refresh, валидирует jti в БД,
    отзывает старый и выдаёт новые токены.
    """
    # Проверяем подпись и структуру JWT
    try:
        payload = verify_refresh_token(refresh_req.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    jti = payload.get("jti")
    user_id = payload.get("sub")

    # Ищем запись в БД
    result = await db.execute(
        select(models.RefreshToken)
        .filter_by(jti=jti, user_id=user_id)
    )
    record = result.scalars().first()
    if not record or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Отзываем старый JTI
    await db.execute(delete(models.RefreshToken).filter_by(jti=jti))
    await db.commit()

    # Получаем пользователя
    user = await db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    # Генерируем новые токены
    return await _create_tokens(user, db)


async def change_password_service(
    user: models.User,
    data: ChangePassword,
    db: AsyncSession
) -> None:
    """
    Проверяем старый пароль, хешируем новый и сохраняем в БД.
    """
    # проверяем старый
    if not bcrypt.checkpw(
        data.old_password.encode("utf-8"),
        user.hashed_password.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # хешируем и меняем
    new_hashed = bcrypt.hashpw(
        data.new_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")
    user.hashed_password = new_hashed
    await db.commit()
