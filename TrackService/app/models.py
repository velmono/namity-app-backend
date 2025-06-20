import ulid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(
        String(26), primary_key=True,
        default=lambda: ulid.new().str,
        unique=True, index=True
    )
    
    user_id: Mapped[str] = mapped_column(
        String(26), index=True
    )
    
    title: Mapped[str] = mapped_column(
        String(200), nullable=False
        )
    
    description: Mapped[str] = mapped_column(
        String(1000), nullable=True
        )
    
    file_key: Mapped[str] = mapped_column(
        String, nullable=False, unique=True
        )
    
    duration_seconds: Mapped[int] = mapped_column(
        Integer,nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )