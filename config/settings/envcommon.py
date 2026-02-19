"""
Environment-specific common settings loaded from environment variables.

This module uses pydantic-settings to load configuration from .env files
and environment variables, providing type validation and defaults.
"""

from typing import Any

from pydantic import Field, field_validator, json
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonEnvSettings(BaseSettings):
    """Common environment settings for all deployment environments."""

    # Security
    SECRET_KEY: str = Field(
        default="django-insecure-change-this-in-production",
        description="Django secret key for cryptographic signing",
    )

    # Debug and Environment
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="local", description="Current environment (local, dev, staging, prod)")

    # Allowed Hosts
    ALLOWED_HOSTS: list[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="List of allowed host/domain names",
    )

    # Internationalization
    LANGUAGE_CODE: str = Field(default="en-us", description="Language code for the application")
    TIME_ZONE: str = Field(default="Asia/Jakarta", description="Time zone for the application")

    # Email Configuration (for production)
    EMAIL_BACKEND: str = Field(
        default="django.core.mail.backends.console.EmailBackend",
        description="Email backend to use",
    )
    EMAIL_HOST: str = Field(default="localhost", description="Email server host")
    EMAIL_PORT: int = Field(default=587, description="Email server port")
    EMAIL_USE_TLS: bool = Field(default=True, description="Use TLS for email")
    EMAIL_HOST_USER: str = Field(default="", description="Email server username")
    EMAIL_HOST_PASSWORD: str = Field(default="", description="Email server password")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def empty_secret_key_to_default(cls, v: Any) -> Any:
        """Convert empty strings to default value."""
        if v == "" or v is None:
            return "django-insecure-change-this-in-production"
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def validate_allowed_hosts(cls, v):
        if isinstance(v, str):
            parsed = json.loads(v)
            # If explicitly set to empty, use defaults
            if parsed == []:
                return ["localhost", "127.0.0.1"]
            return parsed
        # If it's already a list and empty, use defaults
        if isinstance(v, list) and v == []:
            return ["localhost", "127.0.0.1"]
        return v
    
    # Helper properties for Django settings
    @property
    def secret_key(self) -> str:
        """Return secret key in lowercase for Django settings."""
        return self.SECRET_KEY

    @property
    def debug(self) -> bool:
        """Return debug flag in lowercase for Django settings."""
        return self.DEBUG

    @property
    def environment(self) -> str:
        """Return environment in lowercase for Django settings."""
        return self.ENVIRONMENT

    @property
    def allowed_hosts(self) -> list[str]:
        """Return allowed hosts in lowercase for Django settings."""
        return self.ALLOWED_HOSTS

    @property
    def language_code(self) -> str:
        """Return language code in lowercase for Django settings."""
        return self.LANGUAGE_CODE

    @property
    def timezone(self) -> str:
        """Return timezone in lowercase for Django settings."""
        return self.TIME_ZONE

    @property
    def email_backend(self) -> str:
        """Return email backend in lowercase for Django settings."""
        return self.EMAIL_BACKEND

    @property
    def email_host(self) -> str:
        """Return email host in lowercase for Django settings."""
        return self.EMAIL_HOST

    @property
    def email_port(self) -> int:
        """Return email port in lowercase for Django settings."""
        return self.EMAIL_PORT

    @property
    def email_use_tls(self) -> bool:
        """Return email use TLS flag in lowercase for Django settings."""
        return self.EMAIL_USE_TLS

    @property
    def email_host_user(self) -> str:
        """Return email host user in lowercase for Django settings."""
        return self.EMAIL_HOST_USER

    @property
    def email_host_password(self) -> str:
        """Return email host password in lowercase for Django settings."""
        return self.EMAIL_HOST_PASSWORD
