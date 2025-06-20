from pydantic import AnyUrl, Field, SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Namity ProfileService"

    # PostgreSQL
    DATABASE_HOST: str        = Field(..., env="DATABASE_HOST")
    DATABASE_PORT: int        = Field(..., env="DATABASE_PORT")
    DATABASE_USER: str        = Field(..., env="DATABASE_USER")
    DATABASE_PASSWORD: SecretStr = Field(..., env="DATABASE_PASSWORD")
    DATABASE_NAME: str        = Field(..., env="DATABASE_NAME")
    
    PUBLIC_KEY_PATH: str    = Field(..., env="PUBLIC_KEY_PATH")
    ALGORITHM: str          = Field(..., env="ALGORITHM")
    ISSUER: str             = Field(..., env="ISSUER")
    AUDIENCE: str           = Field(..., env="AUDIENCE")

    MINIO_ENDPOINT: str     = Field(..., env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str   = Field(..., env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: SecretStr = Field(..., env="MINIO_SECRET_KEY")
    MINIO_BUCKET: str       = Field(..., env="MINIO_BUCKET")
    MINIO_SECURE: bool      = Field(False, env="MINIO_SECURE")
    MINIO_PUBLIC_ENDPOINT: str = Field(..., env="MINIO_PUBLIC_ENDPOINT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def PUBLIC_KEY(self) -> str:
        if not hasattr(self, "_public_key"):
            self._public_key = None
        if self._public_key is None:
            with open(self.PUBLIC_KEY_PATH, "r", encoding="utf-8") as file:
                self._public_key = file.read()
        return self._public_key
    
    @property
    def DATABASE_URL(self) -> str:
        pwd = self.DATABASE_PASSWORD.get_secret_value()
        return (
            f"postgresql+asyncpg://"
            f"{self.DATABASE_USER}:{pwd}@"
            f"{self.DATABASE_HOST}:{self.DATABASE_PORT}/"
            f"{self.DATABASE_NAME}"
        )

settings = Settings()