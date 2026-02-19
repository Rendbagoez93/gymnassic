"""
Environment Common Settings Module

This module provides environment-specific configuration using Pydantic Settings.
It defines core Django settings that are environment-aware and detachable.

Usage:
    from config.settings.envcommon import get_common_settings
    settings = get_common_settings()
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.monad import get_env

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class __COMMON(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment Configuration
    environment: Literal["local", "production"] = Field(
        default="local",
        description="Current environment (local or production)",
    )

    # Core Django Settings
    secret_key: str = Field(
        default="django-insecure-change-me-in-production",
        description="Django secret key for cryptographic signing",
    )

    debug: bool = Field(
        default=True,
        description="Django DEBUG mode",
    )

    allowed_hosts: str = Field(
        default="localhost,127.0.0.1",
        description="Comma-separated list of allowed hosts",
    )

    # Internationalization
    language_code: str = Field(
        default="en-us",
        description="Django language code",
    )

    timezone: str = Field(
        default="Asia/Jakarta",
        description="Django timezone",
    )

    # Static and Media Files
    static_url: str = Field(
        default="/static/",
        description="Static files URL prefix",
    )

    media_url: str = Field(
        default="/media/",
        description="Media files URL prefix",
    )

    # Email Configuration
    email_backend: str = Field(
        default="django.core.mail.backends.console.EmailBackend",
        description="Django email backend",
    )

    email_host: str = Field(
        default="localhost",
        description="Email server host",
    )

    email_port: int = Field(
        default=587,
        description="Email server port",
    )

    email_use_tls: bool = Field(
        default=True,
        description="Use TLS for email",
    )

    email_host_user: str = Field(
        default="",
        description="Email host user",
    )

    email_host_password: str = Field(
        default="",
        description="Email host password",
    )

    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        if v not in ["local", "production"]:
            raise ValueError(f"Invalid environment: {v}. Must be 'local' or 'production'")
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate secret key in production."""
        if info.data.get("environment") == "production":
            if v == "django-insecure-change-me-in-production":
                raise ValueError(
                    "You must set a secure SECRET_KEY in production environment"
                )
        return v

    def get_allowed_hosts_list(self) -> list[str]:
        """Parse allowed hosts string into a list."""
        if isinstance(self.allowed_hosts, str):
            return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]
        return list(self.allowed_hosts)

    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.environment == "local"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


class LocalSettings(__COMMON):
    environment: Literal["local"] = "local"
    debug: bool = True

    # Development-specific settings
    allowed_hosts: str = "localhost,127.0.0.1,0.0.0.0"


class ProductionSettings(__COMMON):
    environment: Literal["production"] = "production"
    debug: bool = False

    # Production requires explicit configuration
    secret_key: str = Field(
        ...,
        description="Production secret key (must be set via environment variable)",
    )

    # Production email backend
    email_backend: str = Field(
        default="django.core.mail.backends.smtp.EmailBackend",
        description="Production email backend (SMTP)",
    )

    email_host: str = Field(
        default="",
        description="Production email server host (must be set)",
    )

    email_host_user: str = Field(
        default="",
        description="Production email user (must be set)",
    )

    email_host_password: str = Field(
        default="",
        description="Production email password (must be set)",
    )


def get_common_settings() -> __COMMON:
    # Determine environment from environment variables
    env = get_env("DJANGO_ENV", None).unwrap()
    if env is None:
        env = get_env("ENV", "local").unwrap()

    # Normalize environment value
    env = str(env).lower().strip()

    # Return appropriate settings class based on environment
    if env == "production":
        return ProductionSettings()
    else:
        # Default to local for development
        return LocalSettings()


def get_env_type() -> str:
    settings = get_common_settings()
    return settings.environment


# Singleton instance for module-level access
_settings_instance: __COMMON | None = None


def get_settings_instance() -> __COMMON:
    global _settings_instance

    if _settings_instance is None:
        _settings_instance = get_common_settings()

    return _settings_instance


# Export main components
__all__ = [
    "__COMMON",
    "LocalSettings",
    "ProductionSettings",
    "get_common_settings",
    "get_env_type",
    "get_settings_instance",
]
