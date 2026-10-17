from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Library Service Backend Core"
    API_V1_STR: str = "/api/v1"
    ROOT_PATH: str = "/library"  # prefix the gateway strips before forwarding
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "final_project"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    # Room booking rules
    REQUIRE_BOOKING_APPROVAL: bool = True  # False = auto-approve when the slot is free
    MIN_BOOKING_MINUTES: int = 30
    MAX_BOOKING_HOURS: int = 4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
