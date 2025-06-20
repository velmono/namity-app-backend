import uuid
import io
from datetime import timedelta
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from urllib.parse import urlparse, urlunparse, unquote

from app.models import Profile
from app.schemas import ProfileCreate, ProfileUpdate
from app.minio_async import get_minio_client
from app.config import settings

async def get_profile_by_user_id(user_id: str, db: AsyncSession) -> Profile | None:
    result = await db.execute(select(Profile).filter_by(user_id=user_id))
    return result.scalars().first()

async def get_profile_by_slug(slug: str, db: AsyncSession) -> Profile | None:
    result = await db.execute(select(Profile).filter_by(slug=slug))
    return result.scalars().first()

async def create_or_update_profile(
    user_id: str,
    data: ProfileCreate | ProfileUpdate,
    db: AsyncSession
) -> Profile:
    profile = await get_profile_by_user_id(user_id, db)
    
    # Check if slug is provided and unique
    if hasattr(data, 'slug') and data.slug is not None:
        existing = await get_profile_by_slug(data.slug, db)
        if existing and existing.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug already in use"
            )
            
    if not profile:
        profile = Profile(user_id=user_id, **data.model_dump())
        db.add(profile)
    else:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(profile, k, v)
    await db.commit()
    await db.refresh(profile)
    return profile

async def update_avatar_url(
    user_id: str,
    url: str,
    db: AsyncSession
) -> Profile:
    profile = await get_profile_by_user_id(user_id, db)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    profile.avatar_url = url
    await db.commit()
    await db.refresh(profile)
    return profile

async def upload_avatar(user_id: str, file: UploadFile) -> str:
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")
    ext = file.filename.split('.')[-1]
    object_name = f"{user_id}/{uuid.uuid4()}.{ext}"
    async with get_minio_client() as client:
        await client.put_object(
            Bucket=settings.MINIO_BUCKET,
            Key=object_name,
            Body=io.BytesIO(data),
            ContentLength=len(data),
            ContentType=file.content_type,
        )
    return object_name

async def get_avatar_url(object_name: str) -> str:
    """
    Generate a presigned URL for an avatar.
    """
    # Если object_name уже содержит полный URL, извлекаем только путь
    if object_name.startswith('http'):
        parsed = urlparse(unquote(object_name))
        object_name = parsed.path.lstrip('/')
        if object_name.startswith('avatars/'):
            object_name = object_name[8:]  # Убираем 'avatars/' из начала

    async with get_minio_client() as client:
        url = await client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.MINIO_BUCKET, 'Key': object_name},
            ExpiresIn=3600  # 1 hour
        )
        # Заменяем URL MinIO на URL через nginx
        url = url.replace(settings.MINIO_ENDPOINT, 'localhost:8080')
    return url

async def search_profiles(
    query: str,
    limit: int,
    offset: int,
    db: AsyncSession,
) -> list[Profile]:
    """
    Search profiles by username or bio using PostgreSQL full-text search.
    """
    search_query = text("""
        SELECT * FROM profiles 
        WHERE to_tsvector('english', coalesce(display_name, '') || ' ' || coalesce(bio, '')) @@ plainto_tsquery('english', :query)
        ORDER BY ts_rank(to_tsvector('english', coalesce(display_name, '') || ' ' || coalesce(bio, '')), plainto_tsquery('english', :query)) DESC
        LIMIT :limit OFFSET :offset
    """)
    
    result = await db.execute(
        search_query,
        {"query": query, "limit": limit, "offset": offset}
    )
    rows = result.fetchall()
    profiles = []
    for row in rows:
        profiles.append(Profile(**row._mapping))
    return profiles

async def get_random_profiles(limit: int, offset: int, db: AsyncSession) -> list[Profile]:
    """
    Get random profiles for the main page.
    """
    query = select(Profile).order_by(func.random()).offset(offset).limit(limit)
    result = await db.execute(query)
    profiles = result.scalars().all()
    
    for profile in profiles:
        if profile.avatar_url:
            profile.avatar_url = await get_avatar_url(profile.avatar_url)
    
    return profiles