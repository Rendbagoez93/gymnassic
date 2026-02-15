"""
Gym Configuration Module

This module provides core configuration modeling and validation for gym profile settings.
It loads configuration from gym_profile.yaml and validates against gym_schema.json.
"""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

try:
    import yaml
except ImportError:
    # Fallback to pydantic-settings-yaml if yaml is not available
    yaml = None


# Base directory for configuration files
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Address(BaseModel):
    """Address model for Indonesian address format."""

    street_name: str = Field(..., min_length=1, description="Street name and number")
    district_subdistrict: str = Field(
        ..., min_length=1, description="District or subdistrict (Kecamatan/Kelurahan)"
    )
    city: str = Field(..., min_length=1, description="City name (Kota/Kabupaten)")
    province: str = Field(..., min_length=1, description="Province name (Provinsi)")

    model_config = {"extra": "forbid"}


class SocialMedia(BaseModel):
    """Social media handles model."""

    instagram: str = Field(..., description="Instagram handle")
    x: str = Field(..., description="X (Twitter) handle")
    facebook: str = Field(..., description="Facebook page name")

    model_config = {"extra": "forbid"}


class OpeningHours(BaseModel):
    """Operating hours model (24-hour format)."""

    start: str = Field(
        ..., pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Opening time"
    )
    end: str = Field(
        ..., pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Closing time"
    )

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_hours_sequence(self):
        """Validate that end time is after start time."""
        start_h, start_m = map(int, self.start.split(":"))
        end_h, end_m = map(int, self.end.split(":"))

        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m

        if end_minutes <= start_minutes:
            raise ValueError("Opening end time must be after start time")

        return self


DayOfWeek = Literal[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]


class GymProfile(BaseModel):
    """Main gym profile configuration model."""

    gym_name: str = Field(..., min_length=1, description="Name of the gym")
    address: Address = Field(..., description="Gym address in Indonesian format")
    phone_numbers: list[str] = Field(
        ..., min_length=1, description="List of phone numbers"
    )
    email: str = Field(
        ..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        description="Contact email address"
    )
    social_media: SocialMedia = Field(..., description="Social media handles")
    opening_days: list[DayOfWeek] = Field(
        ..., min_length=1, max_length=7, description="Days the gym is open"
    )
    opening_hours: OpeningHours = Field(
        ..., description="Operating hours (24-hour format)"
    )

    model_config = {"extra": "forbid"}

    @field_validator("phone_numbers")
    @classmethod
    def validate_phone_numbers(cls, v: list[str]) -> list[str]:
        """Validate phone number format."""
        import re

        pattern = r"^\+?[0-9\s\-()]+$"
        for phone in v:
            if not re.match(pattern, phone):
                raise ValueError(
                    f"Invalid phone number format: {phone}. "
                    f"Must match pattern: {pattern}"
                )
        return v

    @field_validator("opening_days")
    @classmethod
    def validate_unique_days(cls, v: list[DayOfWeek]) -> list[DayOfWeek]:
        """Validate that opening days are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Opening days must be unique")
        return v


class GymConfigLoader:
    """Loader for gym configuration from YAML file."""

    def __init__(
        self,
        config_path: Path | str | None = None,
        schema_path: Path | str | None = None,
    ):
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to gym_profile.yaml file. Defaults to BASE_DIR/gym_profile.yaml
            schema_path: Path to gym_schema.json file. Defaults to BASE_DIR/gym_schema.json
        """
        self.config_path = (
            Path(config_path) if config_path else BASE_DIR / "gym_profile.yaml"
        )
        self.schema_path = (
            Path(schema_path) if schema_path else BASE_DIR / "gym_schema.json"
        )

    def load_schema(self) -> dict:
        """Load and return the JSON schema."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path, encoding="utf-8") as f:
            return json.load(f)

    def load_config(self) -> dict:
        """Load and return the YAML configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        if yaml is None:
            raise ImportError(
                "PyYAML is required. Install it with: uv add pyyaml"
            ) from None

        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_and_validate(self) -> GymProfile:
        """
        Load the gym configuration from YAML and validate it.

        Returns:
            GymProfile: Validated gym profile configuration

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration validation fails
        """
        config_data = self.load_config()

        # Create and validate the Pydantic model
        try:
            gym_profile = GymProfile(**config_data)
            return gym_profile
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}") from e


# Global configuration loader instance
gym_config_loader = GymConfigLoader()


def load_gym_config() -> GymProfile:
    """
    Load and validate gym configuration from gym_profile.yaml.

    Returns:
        GymProfile: Validated gym profile configuration

    Raises:
        FileNotFoundError: If configuration file doesn't exist
        ValueError: If configuration validation fails
    """
    return gym_config_loader.load_and_validate()


# Load configuration at module import (lazy loading alternative)
def get_gym_config() -> GymProfile:
    """
    Get gym configuration with caching.

    Returns:
        GymProfile: Cached or newly loaded gym profile configuration
    """
    if not hasattr(get_gym_config, "_cached_config"):
        get_gym_config._cached_config = load_gym_config()
    return get_gym_config._cached_config


# Export main components
__all__ = [
    "Address",
    "SocialMedia",
    "OpeningHours",
    "GymProfile",
    "GymConfigLoader",
    "load_gym_config",
    "get_gym_config",
]
