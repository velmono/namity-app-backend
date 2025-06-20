from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from typing import List

from app.services.profile_service import (
    get_profile_by_user_id,
    get_profile_by_slug,
    create_or_update_profile,
    upload_avatar,
    update_avatar_url,
    search_profiles,
    get_random_profiles,
    get_avatar_url,
)
from app.schemas import ProfileCreate, ProfileRead, ProfileUpdate
from app.database import session_dependency
from app.dependencies import get_current_profile

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.get("/me", response_model=ProfileRead)
async def read_my_profile(
    profile = Depends(get_current_profile)
):
    if profile.avatar_url:
        profile.avatar_url = await get_avatar_url(profile.avatar_url)
    return profile

@router.put("/me", response_model=ProfileRead)
async def update_my_profile(
    data: ProfileUpdate,
    db: session_dependency,
    profile = Depends(get_current_profile),
):
    return await create_or_update_profile(profile.user_id, data, db)

@router.get("/search", response_model=list[ProfileRead])
async def search(
    db: session_dependency,
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Search profiles by username or bio.
    """
    profiles = await search_profiles(query, limit, offset, db)
    # Генерируем presigned URL для аватарок
    for profile in profiles:
        if profile.avatar_url:
            profile.avatar_url = await get_avatar_url(profile.avatar_url)
    return profiles

@router.get("/random", response_model=List[ProfileRead])
async def get_random_profiles_endpoint(
    db: session_dependency,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """
    Get random profiles for the main page.
    """
    return await get_random_profiles(limit, offset, db)

@router.get("/{slug}", response_model=ProfileRead)
async def read_profile_by_slug(
    slug: str,
    db: session_dependency,
):
    profile = await get_profile_by_slug(slug, db)
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
    # Генерируем presigned URL для аватарки
    if profile.avatar_url:
        profile.avatar_url = await get_avatar_url(profile.avatar_url)
    return profile

@router.post("/me/avatar", response_model=ProfileRead)
async def change_avatar(
    db: session_dependency,
    file: UploadFile = File(..., description="Avatar image"),
    profile = Depends(get_current_profile),
):
    url = await upload_avatar(profile.user_id, file)
    updated_profile = await update_avatar_url(
        profile.user_id,
        url,
        db
    )
    if updated_profile.avatar_url:
        updated_profile.avatar_url = await get_avatar_url(updated_profile.avatar_url)
    return updated_profile

@router.get("/user/{user_id}", response_model=ProfileRead)
async def read_profile_by_user_id(
    user_id: str,
    db: session_dependency,
):
    profile = await get_profile_by_user_id(user_id, db)
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
    if profile.avatar_url:
        profile.avatar_url = await get_avatar_url(profile.avatar_url)
    return profile