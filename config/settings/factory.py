"""
Environment factory for attaching and detaching environment configurations.
Provides a clean interface for loading different environment settings.
"""

import os
from typing import Literal
from shared.monad import Either
from .envcommon import CommonSettings, DevelopmentSettings, ProductionSettings


EnvironmentType = Literal["development", "production"]


class EnvironmentFactory:
    """Factory for creating and managing environment configurations."""

    _current_env: CommonSettings | None = None
    _env_type: EnvironmentType | None = None

    @classmethod
    def attach(
        cls, env_type: EnvironmentType | None = None
    ) -> CommonSettings:
        # Determine environment type
        if env_type is None:
            env_type = os.getenv("__COMMON_ENVIRONMENT", "development").lower()

        # Validate environment type
        if env_type not in ("development", "production"):
            raise ValueError(
                f"Invalid environment type: {env_type}. Must be 'development' or 'production'."
            )

        # Create appropriate settings instance
        if env_type == "development":
            cls._current_env = DevelopmentSettings()
        else:
            cls._current_env = ProductionSettings()

        cls._env_type = env_type
        return cls._current_env

    @classmethod
    def detach(cls) -> None:
        """Detach the current environment configuration."""
        cls._current_env = None
        cls._env_type = None

    @classmethod
    def current(cls) -> CommonSettings:
        if cls._current_env is None:
            raise RuntimeError(
                "No environment attached. Call attach() first or use get_or_attach()."
            )
        return cls._current_env

    @classmethod
    def get_or_attach(
        cls, env_type: EnvironmentType | None = None
    ) -> CommonSettings:
        if cls._current_env is None:
            return cls.attach(env_type)
        return cls._current_env

    @classmethod
    def is_attached(cls) -> bool:
        """Check if an environment is currently attached."""
        return cls._current_env is not None

    @classmethod
    def current_type(cls) -> EnvironmentType | None:
        """Get the current environment type."""
        return cls._env_type

    @classmethod
    def reload(cls) -> CommonSettings:
        if cls._env_type is None:
            raise RuntimeError("No environment to reload. Call attach() first.")

        env_type = cls._env_type
        cls.detach()
        return cls.attach(env_type)


def load_environment(env_type: EnvironmentType | None = None) -> CommonSettings:
    result = (
        Either(None)
        .bind(lambda: EnvironmentFactory.attach(env_type))
        .unwrap_or(DevelopmentSettings())
    )
    return result


def get_settings() -> CommonSettings:
    return EnvironmentFactory.get_or_attach()
