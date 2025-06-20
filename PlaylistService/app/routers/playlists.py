from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from app.schemas import PlaylistCreate, PlaylistRead, PlaylistUpdate, PlaylistTrackAdd, PlaylistTrackRead
from app.models import Playlist, PlaylistTrack
from app.database import session_dependency
from app.dependencies import get_current_user_id
from app.services.playlist_service import (
    create_playlist as svc_create_playlist,
    list_user_playlists,
    add_track_to_playlist as svc_add_track_to_playlist,
    update_playlist as svc_update_playlist,
    delete_playlist as svc_delete_playlist,
    remove_track_from_playlist as svc_remove_track_from_playlist,
    list_playlist_tracks as svc_list_playlist_tracks,
    search_playlists,
    get_playlist_by_id,
)

router = APIRouter(prefix="/playlists", tags=["playlists"])

@router.post("/", response_model=PlaylistRead, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    data: PlaylistCreate,
    db: session_dependency,
    user_id: str = Depends(get_current_user_id),
):
    playlist = await svc_create_playlist(user_id, data, db)
    return playlist

@router.get("/", response_model=list[PlaylistRead])
async def list_playlists(
    db: session_dependency,
    user_id: str = Depends(get_current_user_id),
):
    playlists = await list_user_playlists(user_id, db)
    return playlists

@router.put("/{playlist_id}", response_model=PlaylistRead)
async def update_playlist(
    playlist_id: str,
    data: PlaylistUpdate,
    db: session_dependency,
    user_id: str = Depends(get_current_user_id),
):
    try:
        playlist = await svc_update_playlist(user_id, playlist_id, data, db)
        return playlist
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Playlist not found or forbidden")

@router.delete("/{playlist_id}", status_code=204)
async def delete_playlist(
    playlist_id: str,
    db: session_dependency,
    user_id: str = Depends(get_current_user_id),
):
    try:
        await svc_delete_playlist(user_id, playlist_id, db)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Playlist not found or forbidden")

@router.post("/{playlist_id}/tracks", response_model=PlaylistTrackRead)
async def add_track_to_playlist(
    playlist_id: str,
    data: PlaylistTrackAdd,
    db: session_dependency,
    user_id: str = Depends(get_current_user_id),
):
    try:
        playlist_track = await svc_add_track_to_playlist(user_id, playlist_id, data, db)
        return playlist_track
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Playlist not found or forbidden")

@router.delete("/{playlist_id}/tracks/{track_id}", status_code=204)
async def remove_track_from_playlist(
    playlist_id: str,
    track_id: str,
    db: session_dependency,
    user_id: str = Depends(get_current_user_id),
):
    try:
        await svc_remove_track_from_playlist(user_id, playlist_id, track_id, db)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{playlist_id}/tracks", response_model=list[PlaylistTrackRead])
async def get_playlist_tracks(
    playlist_id: str,
    db: session_dependency,
    user_id: str = Depends(get_current_user_id),
):
    try:
        tracks = await svc_list_playlist_tracks(user_id, playlist_id, db)
        return tracks
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Playlist not found or forbidden")

@router.get("/search", response_model=list[PlaylistRead])
async def search(
    db: session_dependency,
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Search playlists by title or description.
    """
    return await search_playlists(query, limit, offset, db)

@router.get("/{playlist_id}", response_model=PlaylistRead)
async def get_playlist(
    playlist_id: str,
    db: session_dependency,
):
    playlist = await get_playlist_by_id(playlist_id, db)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist