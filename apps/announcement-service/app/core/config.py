from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "OMS Announcement Service"
    DEBUG: bool = True
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "final_project"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    UPLOAD_DIR: str = "uploads"
    PUBLIC_BASE_URL: str = "http://localhost/announcement"  # gateway URL + route prefix
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_LIST: int = 30      # seconds
    CACHE_TTL_DETAIL: int = 120   # seconds
    RATE_LIMIT_READ: str = "60/minute"
    NOTIFICATION_SERVICE_URL: str | None = None
    INTERNAL_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
