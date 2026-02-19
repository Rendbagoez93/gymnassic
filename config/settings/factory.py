"""
Settings Factory Module

This module provides a unified factory for all Django settings configuration.
It coordinates environment settings, database settings, and gym configuration.

The factory pattern allows for easy extension and testing of different
environment configurations.
"""

from dependency_injector import containers, providers

from .databases import DatabaseSettings, get_database_settings_instance
from .envcommon import __COMMON, get_settings_instance

# Import gym config with error handling
try:
    from .gymconf import GymProfile, get_gym_config
except Exception:
    GymProfile = None
    get_gym_config = None


class SettingsContainer(containers.DeclarativeContainer):
    """
    Dependency injection container for all settings.

    This container coordinates:
    - Environment settings (common Django settings)
    - Database settings
    - Gym configuration (from YAML)

    All settings are singletons to ensure single instances.
    """

    # Environment settings provider
    env_settings = providers.Singleton(get_settings_instance)

    # Database settings provider
    db_settings = providers.Singleton(get_database_settings_instance)

    # Gym config provider (lazy loaded)
    if get_gym_config is not None:
        gym_config = providers.Singleton(get_gym_config)
    else:
        gym_config = providers.Singleton(lambda: None)


# Initialize container
container = SettingsContainer()


def get_settings() -> __COMMON:
    """Get environment settings instance."""
    return container.env_settings()


def get_database_settings() -> DatabaseSettings:
    """Get database settings instance."""
    return container.db_settings()


def get_gym_settings() -> GymProfile | None:
    """Get gym configuration instance."""
    return container.gym_config()


def override_settings(settings_instance: __COMMON) -> None:
    """Override environment settings (for testing)."""
    container.env_settings.override(providers.Singleton(lambda: settings_instance))


def reset_settings() -> None:
    """Reset environment settings override."""
    container.env_settings.reset_override()


# Export main components
__all__ = [
    "SettingsContainer",
    "container",
    "get_settings",
    "get_database_settings",
    "get_gym_settings",
    "override_settings",
    "reset_settings",
]
