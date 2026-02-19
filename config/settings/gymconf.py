"""Gym configuration settings loaded from YAML file.

Provides flexible gym profile configuration including:
- Basic gym information (name, address, contact)
- Dynamic attributes for custom gym properties
"""

from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict
from pydantic_settings_yaml import YamlBaseSettings


class GymAttribute(BaseModel):
    """Dynamic gym attribute with flexible value types."""

    key: str = Field(description="Attribute key/name")
    value: str | int | float | bool | list | dict = Field(description="Attribute value")
    type: Literal["string", "number", "boolean", "array", "object"] = Field(
        default="string", description="Value type"
    )


class GymConfig(YamlBaseSettings):
    """Gym configuration loaded from gym_profile.yaml.

    Supports flexible configuration for gym-specific settings.
    The YAML file can contain any structure, fields defined here
    are the ones explicitly mapped to Python attributes.
    """

    gym_name: str = Field(alias="gym_name", description="Name of the gym")
    address: dict[str, Any] | None = Field(default=None, description="Gym address information")
    phone_numbers: list[str] | None = Field(default=None, description="Contact phone numbers")
    email: str | None = Field(default=None, description="Contact email")
    social_media: dict[str, str] | None = Field(default=None, description="Social media handles")
    opening_days: list[str] | None = Field(default=None, description="Days the gym is open")
    opening_hours: dict[str, str] | None = Field(default=None, description="Opening hours")
    attributes: list[GymAttribute] | None = Field(
        default=None, description="Additional custom attributes"
    )

    model_config = SettingsConfigDict(
        extra="allow",  # Allow extra fields from YAML
        yaml_file_encoding="utf-8",
    )
