import ulid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    # тот же ULID из AuthService
    user_id: Mapped[str] = mapped_column(
        String(26),
        primary_key=True,
        index=True
    )
    
    slug: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(
        String(100), nullable=True
    )
    bio: Mapped[str] = mapped_column(
        String(500), nullable=True
    )
    avatar_url: Mapped[str] = mapped_column(
        String, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )