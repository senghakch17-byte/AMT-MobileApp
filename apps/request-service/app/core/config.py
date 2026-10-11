from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Request Service Backend Core"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "final_project"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    # Reserved for future DB connection string (PostgreSQL/MongoDB)
    DATABASE_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()