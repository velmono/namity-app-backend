import ulid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Playlist(Base):
    __tablename__ = "playlists"
    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=lambda: ulid.new().str, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(26), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    playlist_id: Mapped[str] = mapped_column(String(26), ForeignKey("playlists.id"), primary_key=True)
    track_id: Mapped[str] = mapped_column(String(26), primary_key=True)
    order: Mapped[int] = mapped_column(Integer, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False) 