import ulid
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base



class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(
        String(26),
        primary_key=True,
        default=lambda: ulid.new().str,
        unique=True,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    jti: Mapped[str] = mapped_column(
        String(26),
        unique=True,
        index=True,
        default=lambda: ulid.new().str
    )
    device_name: Mapped[str] = mapped_column(
        String,
        nullable=True
    )
    ip_address: Mapped[str] = mapped_column(
        String,
        nullable=True
    )
    user_agent: Mapped[str] = mapped_column(
        String,
        nullable=True
    )
    issued_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
)
    last_used_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

