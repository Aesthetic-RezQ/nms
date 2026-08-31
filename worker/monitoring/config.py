from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class WorkerSettings(BaseSettings):
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "nms"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    # Default Monitoring Thresholds
    DEFAULT_MONITORING_INTERVAL: int = 15  # seconds
    DEFAULT_PING_TIMEOUT: int = 2          # seconds
    DEFAULT_FAILURE_THRESHOLD: int = 3     # consecutive fails before marking DOWN
    DEFAULT_RECOVERY_THRESHOLD: int = 2    # consecutive successes before marking UP
    DEFAULT_LATENCY_WARNING: float = 100.0 # ms
    DEFAULT_LATENCY_CRITICAL: float = 250.0# ms

    # Worker Engine Parameters
    MAX_CONCURRENT_PINGS: int = 50
    DEVICE_SYNC_INTERVAL: int = 30         # seconds
    PING_COUNT: int = 2                    # packets per check

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        extra = "ignore"

worker_settings = WorkerSettings()
