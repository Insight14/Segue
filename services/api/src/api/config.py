from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/convo_glasses"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/convo_glasses"

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

    # Auth
    AUTH_BYPASS_ENABLED: bool = True
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_CLIENT_ID: str = ""
    COGNITO_REGION: str = "us-east-1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
