import aioboto3
from botocore.config import Config
from app.config import settings

# Создаём сессию aioboto3 один раз
session = aioboto3.Session()

def get_minio_client():
    """
    Возвращает асинхронный контекстный менеджер для клиента S3 (MinIO).
    """
    return session.client(
        's3',
        endpoint_url=(
            f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}"
        ),
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY.get_secret_value(),
        config=Config(signature_version='s3v4'),
    )

async def ensure_bucket_exists():
    """
    Создаёт бакет в MinIO, если он не существует.
    """
    async with get_minio_client() as client:
        response = await client.list_buckets()
        existing = [b['Name'] for b in response.get('Buckets', [])]
        if settings.MINIO_BUCKET not in existing:
            await client.create_bucket(Bucket=settings.MINIO_BUCKET)