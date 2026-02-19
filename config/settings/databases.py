"""
Database Configuration Module

This module handles all database-related configuration for the Django application.
It provides environment-aware database settings using Pydantic for validation.

Usage:
    from config.settings.databases import get_database_config, DATABASES
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.monad import get_env

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment detection
    environment: Literal["local", "production"] = Field(
        default="local",
        description="Current environment (local or production)",
    )

    # Database Configuration
    database_engine: str = Field(
        default="django.db.backends.sqlite3",
        description="Database engine",
    )

    database_name: str = Field(
        default=str(BASE_DIR / "db.sqlite3"),
        description="Database name or path",
    )

    database_user: str = Field(
        default="",
        description="Database user",
    )

    database_password: SecretStr = Field(
        default="",
        description="Database password",
    )

    database_host: str = Field(
        default="",
        description="Database host",
    )

    database_port: str = Field(
        default="",
        description="Database port",
    )

    # Connection pooling and options
    database_conn_max_age: int = Field(
        default=0,
        description="Database connection max age in seconds (0 = no persistent connections)",
    )

    database_conn_health_checks: bool = Field(
        default=False,
        description="Enable connection health checks",
    )

    def get_database_config(self, alias: str = "default") -> dict:
        config = {
            "ENGINE": self.database_engine,
            "NAME": self.database_name,
        }

        # Add optional fields only if they're provided
        if self.database_user:
            config["USER"] = self.database_user

        if self.database_password:
            # Get secret value if it's a SecretStr
            password = self.database_password
            if isinstance(password, SecretStr):
                config["PASSWORD"] = password.get_secret_value()
            else:
                config["PASSWORD"] = str(password)

        if self.database_host:
            config["HOST"] = self.database_host

        if self.database_port:
            config["PORT"] = self.database_port

        # Add connection pooling settings
        if self.database_conn_max_age > 0:
            config["CONN_MAX_AGE"] = self.database_conn_max_age

        if self.database_conn_health_checks:
            config["CONN_HEALTH_CHECKS"] = self.database_conn_health_checks

        return config

    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return "sqlite" in self.database_engine.lower()

    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.database_engine.lower()

    def is_mysql(self) -> bool:
        """Check if using MySQL database."""
        return "mysql" in self.database_engine.lower()


class LocalDatabaseSettings(DatabaseSettings):
    environment: Literal["local"] = "local"
    database_engine: str = "django.db.backends.sqlite3"
    database_name: str = str(BASE_DIR / "db.sqlite3")


class ProductionDatabaseSettings(DatabaseSettings):
    environment: Literal["production"] = "production"

    # Production typically uses PostgreSQL or MySQL
    database_engine: str = Field(
        default="django.db.backends.postgresql",
        description="Production database engine",
    )

    database_name: str = Field(
        ...,
        description="Production database name (must be set)",
    )

    database_user: str = Field(
        ...,
        description="Production database user (must be set)",
    )

    database_password: SecretStr = Field(
        ...,
        description="Production database password (must be set)",
    )

    database_host: str = Field(
        default="localhost",
        description="Production database host",
    )

    database_port: str = Field(
        default="5432",
        description="Production database port",
    )

    # Enable connection pooling in production
    database_conn_max_age: int = Field(
        default=600,
        description="Connection max age in seconds (default: 10 minutes)",
    )

    database_conn_health_checks: bool = Field(
        default=True,
        description="Enable connection health checks in production",
    )


def get_database_settings() -> DatabaseSettings:
    """
    Factory function to get appropriate database settings based on environment.

    Reads DJANGO_ENV or ENV environment variable to determine which
    settings class to instantiate.

    Returns:
        DatabaseSettings: Environment-specific database settings instance
    """
    # Determine environment from environment variables
    env = get_env("DJANGO_ENV", None).unwrap()
    if env is None:
        env = get_env("ENV", "local").unwrap()

    # Normalize environment value
    env = str(env).lower().strip()

    # Return appropriate settings class based on environment
    if env == "production":
        return ProductionDatabaseSettings()
    else:
        # Default to local for development
        return LocalDatabaseSettings()


# Singleton instance for module-level access
_db_settings_instance: DatabaseSettings | None = None


def get_database_settings_instance() -> DatabaseSettings:
    global _db_settings_instance

    if _db_settings_instance is None:
        _db_settings_instance = get_database_settings()

    return _db_settings_instance


def get_database_config(alias: str = "default") -> dict:
    db_settings = get_database_settings_instance()
    return db_settings.get_database_config(alias=alias)


# Django DATABASES configuration
DATABASES = {
    "default": get_database_config(),
}

# Export main components
__all__ = [
    "DatabaseSettings",
    "LocalDatabaseSettings",
    "ProductionDatabaseSettings",
    "get_database_settings",
    "get_database_settings_instance",
    "get_database_config",
    "DATABASES",
]
