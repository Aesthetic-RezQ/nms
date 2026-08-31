from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "nms"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    
    SECRET_KEY: str = "supersecretkey"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    APP_TIMEZONE: str = "Asia/Jakarta"
    APP_NAME: str = "Network Monitoring System"
    
    DEFAULT_MONITORING_INTERVAL: int = 15
    DEFAULT_PING_TIMEOUT: int = 2
    DEFAULT_FAILURE_THRESHOLD: int = 3
    DEFAULT_RECOVERY_THRESHOLD: int = 2
    
    DEFAULT_LATENCY_WARNING: int = 100
    DEFAULT_LATENCY_CRITICAL: int = 250
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
