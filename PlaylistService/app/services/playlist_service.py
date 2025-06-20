from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Playlist, PlaylistTrack
from app.schemas import PlaylistCreate, PlaylistUpdate, PlaylistTrackAdd, PlaylistRead
from sqlalchemy.exc import NoResultFound
from sqlalchemy import select, asc, update, delete
from sqlalchemy.sql import text
from fastapi import HTTPException

async def create_playlist(user_id: str, data: PlaylistCreate, db: AsyncSession) -> Playlist:
    playlist = Playlist(user_id=user_id, title=data.title, description=data.description)
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    return playlist

async def list_user_playlists(user_id: str, db: AsyncSession) -> list[Playlist]:
    result = await db.execute(select(Playlist).where(Playlist.user_id == user_id))
    return result.scalars().all()

async def add_track_to_playlist(user_id: str, playlist_id: str, data: PlaylistTrackAdd, db: AsyncSession) -> PlaylistTrack:
    # Проверяем, что плейлист принадлежит пользователю
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == user_id))
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise NoResultFound("Playlist not found or forbidden")

    # Проверяем, не добавлен ли уже этот трек в плейлист
    result = await db.execute(
        select(PlaylistTrack).where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.track_id == data.track_id
        )
    )
    existing_track = result.scalar_one_or_none()
    if existing_track:
        raise HTTPException(
            status_code=400,
            detail="Track is already in the playlist"
        )

    playlist_track = PlaylistTrack(playlist_id=playlist_id, track_id=data.track_id, order=data.order)
    db.add(playlist_track)
    await db.commit()
    await db.refresh(playlist_track)
    return playlist_track

async def update_playlist(user_id: str, playlist_id: str, data: PlaylistUpdate, db: AsyncSession) -> Playlist:
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == user_id))
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise NoResultFound("Playlist not found or forbidden")
    if data.title is not None:
        playlist.title = data.title
    if data.description is not None:
        playlist.description = data.description
    await db.commit()
    await db.refresh(playlist)
    return playlist

async def delete_playlist(user_id: str, playlist_id: str, db: AsyncSession) -> None:
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == user_id))
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise NoResultFound("Playlist not found or forbidden")
    await db.delete(playlist)
    await db.commit()

async def remove_track_from_playlist(user_id: str, playlist_id: str, track_id: str, db: AsyncSession) -> None:
    # Проверяем, что плейлист принадлежит пользователю
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == user_id))
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise NoResultFound("Playlist not found or forbidden")
    result = await db.execute(select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id, PlaylistTrack.track_id == track_id))
    playlist_track = result.scalar_one_or_none()
    if not playlist_track:
        raise NoResultFound("Track not found in playlist")
    await db.delete(playlist_track)
    await db.commit()

async def list_playlist_tracks(user_id: str, playlist_id: str, db: AsyncSession) -> list[PlaylistTrack]:
    # Проверяем, что плейлист принадлежит пользователю
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise NoResultFound("Playlist not found or forbidden")
    result = await db.execute(
        select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id).order_by(asc(PlaylistTrack.order))
    )
    return result.scalars().all()

async def search_playlists(
    query: str,
    limit: int,
    offset: int,
    db: AsyncSession,
) -> list[PlaylistRead]:
    """
    Search playlists by title or description using PostgreSQL full-text search.
    """
    search_query = text("""
        SELECT p.* FROM playlists p
        WHERE to_tsvector('english', p.title || ' ' || COALESCE(p.description, '')) @@ plainto_tsquery('english', :query)
        ORDER BY ts_rank(to_tsvector('english', p.title || ' ' || COALESCE(p.description, '')), plainto_tsquery('english', :query)) DESC
        LIMIT :limit OFFSET :offset
    """)
    
    result = await db.execute(
        search_query,
        {"query": query, "limit": limit, "offset": offset}
    )
    playlists = result.mappings().all()
    
    # Convert dictionary results to Playlist models
    playlist_models = [Playlist(**playlist) for playlist in playlists]
    
    # Convert Playlist models to PlaylistRead schemas
    return [PlaylistRead.model_validate(playlist) for playlist in playlist_models]

async def get_playlist_by_id(playlist_id: str, db: AsyncSession) -> Playlist | None:
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    return result.scalar_one_or_none()