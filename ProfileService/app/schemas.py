from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ProfileCreate(BaseModel):
    slug: str = Field(..., min_length=3, max_length=50)
    display_name: Optional[str] = None
    bio: Optional[str] = None

class ProfileUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=3, max_length=50)
    display_name: Optional[str] = None
    bio: Optional[str] = None

class ProfileRead(BaseModel):
    user_id: str
    slug: str
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}