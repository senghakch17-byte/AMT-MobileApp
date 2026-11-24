from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Request Service Backend Core"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "final_project"
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = 10000
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    NOTIFICATION_SERVICE_URL: str | None = None
    INTERNAL_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
