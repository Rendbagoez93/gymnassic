"""
Common environment settings using pydantic-settings.
All environment variables use '__COMMON' prefix.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """Base settings class for all environments."""

    model_config = SettingsConfigDict(
        env_prefix="__COMMON_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Django settings
    secret_key: str = Field(
        default="django-insecure-default-key-change-in-production",
        description="Django SECRET_KEY",
    )
    debug: bool = Field(default=False, description="Django DEBUG mode")
    allowed_hosts: str = Field(
        default="localhost,127.0.0.1",
        description="Django ALLOWED_HOSTS (comma-separated)",
    )

    # Environment identification
    environment: str = Field(
        default="development",
        description="Current environment (development/production)",
    )

    # Database settings
    database_url: str = Field(
        default="sqlite:///db.sqlite3",
        description="Database connection URL",
    )
    database_name: str | None = Field(
        default=None,
        description="Database name (optional, extracted from URL if not provided)",
    )

    # Application settings
    log_level: str = Field(default="INFO", description="Logging level")
    timezone: str = Field(default="UTC", description="Application timezone")
    language_code: str = Field(default="en-us", description="Default language code")

    def get_allowed_hosts_list(self) -> list[str]:
        """Convert allowed_hosts string to list."""
        if isinstance(self.allowed_hosts, str):
            return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]
        return self.allowed_hosts

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment name."""
        valid_envs = ["development", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v_lower


class DevelopmentSettings(CommonSettings):
    """Development environment settings."""

    model_config = SettingsConfigDict(
        env_prefix="__COMMON_",
        env_file=".env.development",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    debug: bool = Field(default=True, description="Django DEBUG mode for development")
    environment: str = Field(default="development", description="Development environment")
    log_level: str = Field(default="DEBUG", description="Debug logging for development")


class ProductionSettings(CommonSettings):
    """Production environment settings."""

    model_config = SettingsConfigDict(
        env_prefix="__COMMON_",
        env_file=".env.production",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    debug: bool = Field(default=False, description="Django DEBUG mode for production")
    environment: str = Field(default="production", description="Production environment")
    secret_key: str = Field(
        ...,  # Required in production
        description="Django SECRET_KEY - MUST be set in production",
    )
    allowed_hosts: str = Field(
        default="",  # Empty by default, must be configured
        description="Django ALLOWED_HOSTS for production (comma-separated)",
    )
