from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ulid import ULID

class PlaylistBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistUpdate(PlaylistBase):
    title: Optional[str] = Field(None, min_length=1, max_length=100)

class PlaylistTrackAdd(BaseModel):
    track_id: str = Field(..., min_length=1)
    order: int = Field(0, ge=0)  # По умолчанию 0, не может быть отрицательным

class PlaylistTrackRead(BaseModel):
    track_id: str
    added_at: datetime

    class Config:
        from_attributes = True

class PlaylistRead(PlaylistBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    tracks: List[PlaylistTrackRead] = []

    class Config:
        from_attributes = True 