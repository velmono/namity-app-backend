from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = Field(..., env="PROJECT_NAME")
    
    DATABASE_NAME: str = Field(..., env="DATABASE_NAME")
    DATABASE_HOST: str = Field(..., env="DATABASE_HOST")
    DATABASE_PORT: int = Field(..., env="DATABASE_PORT")
    DATABASE_USER: str = Field(..., env="DATABASE_USER")
    DATABASE_PASSWORD: SecretStr = Field(..., env="DATABASE_PASSWORD")

    PRIVATE_KEY_PATH: str = Field(..., env="PRIVATE_KEY_PATH")
    PUBLIC_KEY_PATH: str = Field(..., env="PUBLIC_KEY_PATH")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(..., env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(..., env="REFRESH_TOKEN_EXPIRE_DAYS")
    ALGORITHM: str = Field(..., env="ALGORITHM")
    ISSUER: str = Field(..., env="ISSUER")
    
    @property
    def PRIVATE_KEY(self) -> str:
        if not hasattr(self, "_private_key"):
            self._private_key = None
        if self._private_key is None:
            with open(self.PRIVATE_KEY_PATH, "r", encoding="utf-8") as file:
                self._private_key = file.read()
        return self._private_key

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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()