from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/convo_glasses"

    # S3 / MinIO
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "convo-glasses-documents"
    S3_REGION: str = "us-east-1"

    # SQS / ElasticMQ
    SQS_ENDPOINT_URL: str = "http://localhost:9324"
    SQS_QUEUE_URL: str = "http://localhost:9324/000000000000/convo-glasses-jobs"
    SQS_REGION: str = "us-east-1"

    # Poll settings
    POLL_WAIT_TIME_SECONDS: int = 10
    MAX_MESSAGES_PER_POLL: int = 5


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
