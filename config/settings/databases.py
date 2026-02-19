"""
Database configuration settings for Django.

This module provides database configuration using Pydantic for type safety
and validation. Supports SQLite and PostgreSQL databases with environment-based
configuration.
"""

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBEngineEnum(StrEnum):
    """Supported database engines."""

    SQLITE = "django.db.backends.sqlite3"
    POSTGRES = "django.db.backends.postgresql"


class BaseDatabaseSettings(BaseSettings):
    """Base database settings shared across all database types."""

    engine: DBEngineEnum = Field(
        default=DBEngineEnum.SQLITE,
        serialization_alias="engine",
    )

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        extra="ignore",
        frozen=True,
        alias_generator=lambda field_name: field_name.upper(),
        populate_by_name=True,
        env_file=".env",
    )

    @field_validator("engine", mode="before")
    @classmethod
    def validate_engine(cls, v: Any) -> DBEngineEnum:
        if isinstance(v, DBEngineEnum):
            return v

        valid_names = [member.name for member in DBEngineEnum]
        valid_values = [member.value for member in DBEngineEnum]

        if isinstance(v, str):
            # Try to match by name (case-insensitive)
            try:
                return DBEngineEnum[v.upper()]
            except KeyError:
                pass

            # Try to match by value
            for enum_member in DBEngineEnum:
                if v == enum_member.value:
                    return enum_member

        raise PydanticCustomError(
            "enum",
            f"Input should be one of the enum names: {valid_names} or one of the enum values: {valid_values}",
            {
                "input": v,
                "valid_names": valid_names,
                "valid_values": valid_values,
            },
        )


class SqliteDatabaseSettings(BaseDatabaseSettings):
    """Settings for SQLite database."""

    engine: DBEngineEnum = Field(
        default=DBEngineEnum.SQLITE,
        serialization_alias="ENGINE",
    )
    name: str = Field(
        default=(Path(__file__).resolve().parent.parent.parent / "db.sqlite3").as_posix(),
        serialization_alias="NAME",
    )

    @field_validator("name", mode="before")
    @classmethod
    def empty_str_to_default(cls, v: Any) -> Any:
        """Convert empty strings to use default value by raising validation error."""
        # When empty string is provided, skip it so default will be used
        if v == "" or v is None:
            # Return the actual default value
            return (Path(__file__).resolve().parent.parent.parent / "db.sqlite3").as_posix()
        return v


class PostgresDatabaseSettings(BaseDatabaseSettings):
    """Settings for PostgreSQL database."""

    engine: DBEngineEnum = Field(
        default=DBEngineEnum.POSTGRES,
        serialization_alias="ENGINE",
    )
    port: int = Field(
        default=5432,
        serialization_alias="PORT",
    )
    host: str = Field(
        default="localhost",
        serialization_alias="HOST",
    )
    password: str = Field(
        default="postgres",
        serialization_alias="PASSWORD",
    )
    user: str = Field(
        default="postgres",
        serialization_alias="USER",
    )
    name: str = Field(
        default="gymnassic",
        serialization_alias="NAME",
    )

    @field_validator("name", mode="before")
    @classmethod
    def empty_name_to_default(cls, v: Any) -> Any:
        """Convert empty strings to default value."""
        if v == "" or v is None:
            return "gymnassic"
        return v

    @field_validator("password", mode="before")
    @classmethod
    def empty_password_to_default(cls, v: Any) -> Any:
        """Convert empty strings to default value."""
        if v == "" or v is None:
            return "postgres"
        return v

    @field_validator("user", mode="before")
    @classmethod
    def empty_user_to_default(cls, v: Any) -> Any:
        """Convert empty strings to default value."""
        if v == "" or v is None:
            return "postgres"
        return v

    @field_validator("host", mode="before")
    @classmethod
    def empty_host_to_default(cls, v: Any) -> Any:
        """Convert empty strings to default value."""
        if v == "" or v is None:
            return "localhost"
        return v


class DjangoDatabases(BaseModel):
    """Django database settings container."""

    default: PostgresDatabaseSettings | SqliteDatabaseSettings

