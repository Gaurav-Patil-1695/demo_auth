from __future__ import annotations

from pydantic import AnyUrl, EmailStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str

    # ------------------------------------------------------------------ #
    # JWT
    # ------------------------------------------------------------------ #
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_TTL_MINUTES: int = 15

    # ------------------------------------------------------------------ #
    # Bcrypt
    # ------------------------------------------------------------------ #
    BCRYPT_ROUNDS: int = 12

    # ------------------------------------------------------------------ #
    # Password reset token
    # ------------------------------------------------------------------ #
    RESET_TOKEN_TTL_MINUTES: int = 30

    # ------------------------------------------------------------------ #
    # Refresh token
    # ------------------------------------------------------------------ #
    REFRESH_TOKEN_TTL_DAYS: int = 7
    REFRESH_TOKEN_TTL_DAYS_REMEMBER: int = 30

    # ------------------------------------------------------------------ #
    # SMTP
    # ------------------------------------------------------------------ #
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_ADDRESS: EmailStr
    SMTP_USE_TLS: bool = True

    # ------------------------------------------------------------------ #
    # Rate limiting
    # ------------------------------------------------------------------ #
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 10
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60
    RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS: int = 3600

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def database_url_must_not_be_empty(cls, v: object) -> object:
        if isinstance(v, str) and not v.strip():
            raise ValueError("DATABASE_URL must not be empty")
        return v

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def jwt_secret_must_not_be_empty(cls, v: object) -> object:
        if isinstance(v, str) and not v.strip():
            raise ValueError("JWT_SECRET_KEY must not be empty")
        return v

    @field_validator("BCRYPT_ROUNDS", mode="before")
    @classmethod
    def bcrypt_rounds_minimum(cls, v: object) -> object:
        if isinstance(v, int) and v < 12:
            raise ValueError("BCRYPT_ROUNDS must be at least 12")
        if isinstance(v, str) and int(v) < 12:
            raise ValueError("BCRYPT_ROUNDS must be at least 12")
        return v

    @field_validator("SMTP_PORT", mode="before")
    @classmethod
    def smtp_port_valid_range(cls, v: object) -> object:
        port = int(v) if isinstance(v, str) else v
        if not isinstance(port, int) or not (1 <= port <= 65535):
            raise ValueError("SMTP_PORT must be between 1 and 65535")
        return v


def _load_settings() -> Settings:
    """Instantiate Settings eagerly so the process fails fast on misconfiguration."""
    return Settings()  # type: ignore[call-arg]


settings: Settings = _load_settings()
