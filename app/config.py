from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Marginalia"
    APP_ENV: str = "local"
    APP_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./marginalia.db"
    LOG_LEVEL: str = "INFO"

    # Newsletter — Claude summarisation
    ANTHROPIC_API_KEY: str = ""

    # Newsletter — SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    MAIL_FROM: str = ""
    MAIL_TO: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
