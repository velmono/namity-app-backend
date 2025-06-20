from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Namity PlaylistService"

    DATABASE_HOST: str        = Field(..., env="DATABASE_HOST")
    DATABASE_PORT: int        = Field(..., env="DATABASE_PORT")
    DATABASE_USER: str        = Field(..., env="DATABASE_USER")
    DATABASE_PASSWORD: SecretStr = Field(..., env="DATABASE_PASSWORD")
    DATABASE_NAME: str        = Field(..., env="DATABASE_NAME")

    PUBLIC_KEY_PATH: str    = Field(..., env="PUBLIC_KEY_PATH")
    ALGORITHM: str          = Field(..., env="ALGORITHM")
    ISSUER: str             = Field(..., env="ISSUER")
    AUDIENCE: str           = Field(..., env="AUDIENCE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

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