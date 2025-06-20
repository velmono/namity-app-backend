from fastapi import APIRouter, Depends, File, UploadFile, status, HTTPException, Query, Form
from fastapi.responses import StreamingResponse
from fastapi import Request
from typing import List

from app.dependencies import get_current_user_id
from app.models import Track
from app.config import settings
from app.minio_async import get_minio_client

from app.database import session_dependency
from app.schemas import TrackCreate, TrackRead, TrackUpdate
from app.services.track_service import (
    create_track,
    list_user_tracks,
    get_track,
    update_track,
    delete_track,
    stream_track_service,
    search_tracks,
    get_random_tracks,
)

router = APIRouter(prefix="/tracks", tags=["tracks"])

@router.post(
    "/",
    response_model=TrackRead,
    status_code=status.HTTP_201_CREATED
)
async def upload(
    db: session_dependency,
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    return await create_track(user_id, TrackCreate(title=title, description=description), file, db)

@router.get("/", response_model=list[TrackRead])
async def list_my(
    db: session_dependency,
    user_id: str = Depends(get_current_user_id),
):
    return await list_user_tracks(user_id, db)

@router.get("/search", response_model=list[TrackRead])
async def search(
    db: session_dependency,
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Search tracks by title or description.
    """
    return await search_tracks(query, limit, offset, db)

@router.get("/random", response_model=List[TrackRead])
async def get_random_tracks_endpoint(
    db: session_dependency,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """
    Get random tracks for the main page.
    """
    return await get_random_tracks(limit, offset, db)

@router.get("/{track_id}/stream")
async def stream_track(
    request: Request,
    db: session_dependency,
    track_id: str,
):
    return await stream_track_service(request, db, track_id)

@router.get("/{track_id}", response_model=TrackRead)
async def read(
    db: session_dependency,
    track_id: str,
):
    track = await get_track(track_id, db)
    return track

@router.put("/{track_id}", response_model=TrackRead)
async def modify(
    db: session_dependency,
    track_id: str,
    data: TrackUpdate,
    user_id: str = Depends(get_current_user_id),
):
    track = await get_track(track_id, db)
    if track.user_id != user_id:
        raise HTTPException(403, "Forbidden")
    return await update_track(track_id, data, db)

@router.delete("/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove(
    db: session_dependency,
    track_id: str,
    user_id: str = Depends(get_current_user_id),
):
    track = await get_track(track_id, db)
    if track.user_id != user_id:
        raise HTTPException(403, "Forbidden")
    await delete_track(track_id, db)
    return

@router.get("/user/{user_id}", response_model=list[TrackRead])
async def list_user_tracks_endpoint(
    db: session_dependency,
    user_id: str,
):
    """
    Get all tracks uploaded by a specific user.
    """
    return await list_user_tracks(user_id, db)