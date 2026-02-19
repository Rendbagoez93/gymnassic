"""Settings factory module for dependency injection and configuration management.

Provides factory functions to create and manage application settings including:
- Environment settings (CommonEnvSettings)
- Database configuration (DjangoDatabases)
- Gym configuration (GymConfig)
"""

from pathlib import Path

from dependency_injector import containers, providers

from .databases import (
    BaseDatabaseSettings,
    DBEngineEnum,
    DjangoDatabases,
    PostgresDatabaseSettings,
    SqliteDatabaseSettings,
)
from .envcommon import CommonEnvSettings
from .gymconf import GymConfig


class DbContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    db_factory = providers.FactoryAggregate(
        {
            DBEngineEnum.SQLITE: providers.Factory(SqliteDatabaseSettings),
            DBEngineEnum.POSTGRES: providers.Factory(PostgresDatabaseSettings),
        }
    )
    fct = providers.Factory(db_factory, config.engine)
    django_databases = providers.Singleton(
        DjangoDatabases,
        default=fct,
    )


def get_django_dbs() -> DjangoDatabases:
    """Get the Django database settings."""
    db_container = DbContainer()
    db_container.config.from_pydantic(BaseDatabaseSettings())
    return db_container.django_databases()


def get_django_db_dict() -> dict:
    """Get the Django database settings as a dictionary."""
    db = get_django_dbs()
    return db.model_dump(mode="json", by_alias=True)


def get_settings() -> CommonEnvSettings:
    return CommonEnvSettings()


def get_gym_settings() -> GymConfig:
    # Get the project root directory (three levels up from settings/factory.py)
    project_root = Path(__file__).resolve().parent.parent.parent
    gym_config_path = project_root / "gym_profile.yaml"

    if not gym_config_path.exists():
        raise FileNotFoundError(f"Gym configuration file not found: {gym_config_path}")

    return GymConfig(_yaml_files=[gym_config_path])
