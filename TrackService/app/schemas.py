from pydantic import BaseModel, Field, computed_field
from datetime import datetime

class TrackCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None

class TrackRead(BaseModel):
    id: str
    title: str
    description: str | None
    duration_seconds: int
    created_at: datetime
    updated_at: datetime
    user_id: str

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def stream_url(self) -> str:
        # этот метод будет вызван Pydantic автоматически
        return f"/tracks/{self.id}/stream"

class TrackUpdate(BaseModel):
    title: str | None = None
    description: str | None = None