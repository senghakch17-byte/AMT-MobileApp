from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "OMS User Service"
    API_V1_STR: str = ""
    ROOT_PATH: str = "/user"  # prefix the gateway strips before forwarding
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "final_project"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    UPLOAD_DIR: str = "uploads"
    PUBLIC_BASE_URL: str = "http://localhost/user"  # gateway URL + route prefix
    MAX_DOCUMENT_MB: int = 10
    REGISTRATION_SERVICE_URL: str | None = None
    INTERNAL_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
