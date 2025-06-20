from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from fastapi import Depends
from typing import AsyncGenerator, Annotated
from app.config import settings

class Base(DeclarativeBase):
    pass

_engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    echo=True
)

_async_session = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def _get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session() as session:
        yield session

session_dependency = Annotated[AsyncSession, Depends(_get_db)]