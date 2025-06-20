import uuid, io
from pydub import AudioSegment
from fastapi import HTTPException, status, UploadFile
import re
from urllib.parse import urlparse, urlunparse
from fastapi.responses import StreamingResponse
from fastapi import Request

from sqlalchemy import select, delete, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.minio_async import get_minio_client

from app.models import Track
from app.schemas import TrackCreate, TrackUpdate
from app.config import settings

    
async def ensure_bucket_exists():
    """
    Создаёт бакет в MinIO, если он не существует.
    """
    async with get_minio_client() as client:
        response = await client.list_buckets()
        existing = [b['Name'] for b in response.get('Buckets', [])]
        if settings.MINIO_BUCKET not in existing:
            await client.create_bucket(Bucket=settings.MINIO_BUCKET)

async def upload_file_to_minio(user_id: str, file: UploadFile) -> tuple[str, int]:
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")

    try:
        mime = file.content_type
        fmt = mime.split("/")[-1]
        audio = AudioSegment.from_file(io.BytesIO(data), format="mp3")
        duration_sec = int(len(audio) / 1000)
        out_buf = io.BytesIO()
        audio.export(out_buf, format="mp3", bitrate="192k")
        out_buf.seek(0)
    except Exception as e:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Cannot process audio file: {e}"
        )

    key = f"{user_id}/{uuid.uuid4()}.mp3"


    async with get_minio_client() as client:
        await client.put_object(
            Bucket=settings.MINIO_BUCKET,
            Key=key,
            Body=out_buf,
            ContentType="audio/mpeg",
            ContentLength=len(out_buf.getbuffer()),
        )

    return key, duration_sec

async def create_track(
    user_id: str,
    data: TrackCreate,
    file: UploadFile,
    db: AsyncSession
) -> Track:

    key, duration = await upload_file_to_minio(user_id, file)

    # Создаём запись с duration_seconds
    track = Track(
        user_id=user_id,
        title=data.title,
        description=data.description,
        file_key=key,
        duration_seconds=duration
    )
    db.add(track)
    await db.commit()
    await db.refresh(track)

    return track

async def list_user_tracks(user_id: str, db: AsyncSession) -> list[Track]:
    result = await db.execute(select(Track).filter_by(user_id=user_id))
    return result.scalars().all()

async def get_track(track_id: str, db: AsyncSession) -> Track:
    track = await db.get(Track, track_id)
    if not track:
        raise HTTPException(404, "Track not found")
    # generate presigned URL
    async with get_minio_client() as client:
        url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.MINIO_BUCKET, "Key": track.file_key},
            ExpiresIn=3600
        )
    parsed = urlparse(url)
    public_url = urlunparse(parsed._replace(netloc=settings.MINIO_PUBLIC_ENDPOINT))
    track.file_url = public_url
    return track

async def update_track(
    track_id: str, data: TrackUpdate, db: AsyncSession
) -> Track:
    track = await db.get(Track, track_id)
    if not track:
        raise HTTPException(404, "Track not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(track, k, v)
    await db.commit()
    await db.refresh(track)
    return await get_track(track_id, db)

async def delete_track(track_id: str, db: AsyncSession) -> None:
    track = await db.get(Track, track_id)
    if not track:
        raise HTTPException(404, "Track not found")
    # можно в фоне удалить объект из MinIO, но опустим
    await db.execute(delete(Track).filter_by(id=track_id))
    await db.commit()

async def stream_track_service(request: Request, db: AsyncSession, track_id: str):
    track: Track | None = await db.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    key = track.file_key

    async def file_iterator(chunk_size=1024 * 1024):
        async with get_minio_client() as client:
            s3_obj = await client.get_object(
                Bucket=settings.MINIO_BUCKET, Key=key
            )
            body = s3_obj["Body"]
            try:
                while True:
                    chunk = await body.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

    range_header = request.headers.get("range")
    if range_header:
        async with get_minio_client() as client:
            s3_obj = await client.head_object(
                Bucket=settings.MINIO_BUCKET, Key=key
            )
            content_length = s3_obj.get("ContentLength")
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else content_length - 1
            length = end - start + 1
            headers = {
                "Content-Disposition": f'inline; filename="{track_id}.mp3"',
                "Accept-Ranges": "bytes",
                "Content-Range": f"bytes {start}-{end}/{content_length}",
                "Content-Length": str(length),
            }
            async def range_iterator(chunk_size=1024 * 1024):
                async with get_minio_client() as client:
                    s3_obj = await client.get_object(
                        Bucket=settings.MINIO_BUCKET,
                        Key=key,
                        Range=f"bytes={start}-{end}"
                    )
                    body = s3_obj["Body"]
                    remaining = length
                    try:
                        while remaining > 0:
                            chunk = await body.read(min(chunk_size, remaining))
                            if not chunk:
                                break
                            yield chunk
                            remaining -= len(chunk)
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Error: {e}")
            return StreamingResponse(
                range_iterator(),
                status_code=206,
                media_type="audio/mpeg",
                headers=headers
            )

    async with get_minio_client() as client:
        s3_obj = await client.head_object(
            Bucket=settings.MINIO_BUCKET, Key=key
        )
        content_length = s3_obj.get("ContentLength")

    headers = {
        "Content-Disposition": f'inline; filename="{track_id}.mp3"',
        "Accept-Ranges": "bytes",
        "Content-Type": "audio/mpeg",
        "Content-Length": str(content_length),
    }
    if content_length:
        headers["Content-Length"] = str(content_length)

    return StreamingResponse(
        file_iterator(),
        media_type="audio/mpeg",
        headers=headers
    )

async def search_tracks(
    query: str,
    limit: int,
    offset: int,
    db: AsyncSession,
) -> list[Track]:
    """
    Search tracks by title or description using ILIKE (ORM).
    """
    stmt = select(Track).where(
        or_(
            Track.title.ilike(f"%{query}%"),
            Track.description.ilike(f"%{query}%")
        )
    ).order_by(Track.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_random_tracks(limit: int, offset: int, db: AsyncSession) -> list[Track]:
    """
    Get random tracks for the main page.
    """
    query = select(Track).order_by(func.random()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()