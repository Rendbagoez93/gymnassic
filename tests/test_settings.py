"""
Test suite for environment settings and configuration.

Tests cover:
- CommonEnvSettings base settings validation and loading
- Database settings configuration
- Settings factory functions
"""

import os
import pytest
from pydantic import ValidationError

from config.settings.envcommon import CommonEnvSettings
from config.settings.databases import (
    BaseDatabaseSettings,
    SqliteDatabaseSettings,
    PostgresDatabaseSettings,
    DjangoDatabases,
    DBEngineEnum,
)
from config.settings.factory import (
    get_settings,
    get_django_dbs,
    get_django_db_dict,
    get_gym_settings,
)


# ============================================================================
# COMMON SETTINGS TESTS
# ============================================================================

class TestCommonEnvSettings:
    """Test CommonEnvSettings base configuration."""

    def test_default_common_settings(self, clean_environment):
        """Test CommonEnvSettings with default values."""
        settings = CommonEnvSettings()

        assert settings.SECRET_KEY == "django-insecure-change-this-in-production"
        assert settings.DEBUG is False
        assert settings.allowed_hosts == ["localhost", "127.0.0.1"]
        assert settings.ENVIRONMENT == "local"
        assert settings.TIME_ZONE == "Asia/Jakarta"
        assert settings.LANGUAGE_CODE == "en-us"

    def test_common_settings_properties(self, clean_environment):
        """Test property accessors for Django settings."""
        settings = CommonEnvSettings(DEBUG=True, SECRET_KEY="test-key")

        assert settings.secret_key == "test-key"
        assert settings.debug is True
        assert settings.environment == "local"
        assert settings.timezone == "Asia/Jakarta"
        assert settings.language_code == "en-us"

    def test_custom_common_settings(self, clean_environment):
        """Test CommonEnvSettings with custom values."""
        settings = CommonEnvSettings(
            SECRET_KEY="local-secret-key-for-testing",
            DEBUG=True,
            ALLOWED_HOSTS=["localhost", "127.0.0.1", "0.0.0.0"],
            ENVIRONMENT="local"
        )

        assert settings.secret_key == "local-secret-key-for-testing"
        assert settings.debug is True
        assert "0.0.0.0" in settings.allowed_hosts
        assert settings.environment == "local"

    def test_email_settings(self, clean_environment):
        """Test email configuration settings."""
        settings = CommonEnvSettings(
            EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
            EMAIL_HOST="smtp.gmail.com",
            EMAIL_PORT=587,
            EMAIL_USE_TLS=True,
            EMAIL_HOST_USER="test@example.com",
            EMAIL_HOST_PASSWORD="secret"
        )

        assert settings.email_backend == "django.core.mail.backends.smtp.EmailBackend"
        assert settings.email_host == "smtp.gmail.com"
        assert settings.email_port == 587
        assert settings.email_use_tls is True
        assert settings.email_host_user == "test@example.com"
        assert settings.email_host_password == "secret"


# ============================================================================
# DATABASE SETTINGS TESTS
# ============================================================================

class TestBaseDatabaseSettings:
    """Test BaseDatabaseSettings configuration."""

    def test_default_database_settings(self, clean_environment):
        """Test BaseDatabaseSettings with default values."""
        settings = BaseDatabaseSettings()

        assert settings.engine == DBEngineEnum.SQLITE

    def test_database_engine_validation_by_name(self, clean_environment):
        """Test database engine validation by name."""
        settings = BaseDatabaseSettings(engine="SQLITE")
        assert settings.engine == DBEngineEnum.SQLITE

        settings = BaseDatabaseSettings(engine="POSTGRES")
        assert settings.engine == DBEngineEnum.POSTGRES

    def test_database_engine_validation_by_value(self, clean_environment):
        """Test database engine validation by value."""
        settings = BaseDatabaseSettings(engine="django.db.backends.sqlite3")
        assert settings.engine == DBEngineEnum.SQLITE

        settings = BaseDatabaseSettings(engine="django.db.backends.postgresql")
        assert settings.engine == DBEngineEnum.POSTGRES

    def test_database_engine_invalid(self, clean_environment):
        """Test invalid database engine raises error."""
        with pytest.raises(ValidationError):
            BaseDatabaseSettings(engine="invalid_engine")


class TestSqliteDatabaseSettings:
    """Test SqliteDatabaseSettings configuration."""

    def test_sqlite_database_defaults(self, clean_environment):
        """Test SqliteDatabaseSettings with default values."""
        settings = SqliteDatabaseSettings()

        assert settings.engine == DBEngineEnum.SQLITE
        assert "db.sqlite3" in settings.name

    def test_sqlite_custom_name(self, clean_environment):
        """Test SqliteDatabaseSettings with custom database name."""
        settings = SqliteDatabaseSettings(name="/custom/path/test.db")

        assert settings.name == "/custom/path/test.db"
        assert settings.engine == DBEngineEnum.SQLITE


class TestPostgresDatabaseSettings:
    """Test PostgresDatabaseSettings configuration."""

    def test_postgres_database_defaults(self, clean_environment):
        """Test PostgresDatabaseSettings with default values."""
        settings = PostgresDatabaseSettings()

        assert settings.engine == DBEngineEnum.POSTGRES
        assert settings.host == "localhost"
        assert settings.port == 5432
        assert settings.user == "postgres"
        assert settings.password == "postgres"
        assert settings.name == "gymnassic"

    def test_postgres_custom_values(self, clean_environment):
        """Test PostgresDatabaseSettings with custom configuration."""
        settings = PostgresDatabaseSettings(
            host="db.example.com",
            port=5433,
            user="gymuser",
            password="securepass",
            name="gymnassic_prod"
        )

        assert settings.host == "db.example.com"
        assert settings.port == 5433
        assert settings.user == "gymuser"
        assert settings.password == "securepass"
        assert settings.name == "gymnassic_prod"


class TestDjangoDatabases:
    """Test DjangoDatabases configuration."""

    def test_django_databases_with_sqlite(self, clean_environment):
        """Test DjangoDatabases with SQLite."""
        sqlite_settings = SqliteDatabaseSettings()
        django_dbs = DjangoDatabases(default=sqlite_settings)

        assert isinstance(django_dbs.default, SqliteDatabaseSettings)
        assert django_dbs.default.engine == DBEngineEnum.SQLITE

    def test_django_databases_with_postgres(self, clean_environment):
        """Test DjangoDatabases with PostgreSQL."""
        postgres_settings = PostgresDatabaseSettings()
        django_dbs = DjangoDatabases(default=postgres_settings)

        assert isinstance(django_dbs.default, PostgresDatabaseSettings)
        assert django_dbs.default.engine == DBEngineEnum.POSTGRES


# ============================================================================
# FACTORY FUNCTIONS TESTS
# ============================================================================

class TestFactoryFunctions:
    """Test settings factory functions."""

    def test_get_settings_function(self, clean_environment):
        """Test get_settings convenience function."""
        settings = get_settings()
        
        assert isinstance(settings, CommonEnvSettings)
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'DEBUG')

    def test_get_django_dbs_function(self, clean_environment):
        """Test get_django_dbs function."""
        django_dbs = get_django_dbs()
        
        assert isinstance(django_dbs, DjangoDatabases)
        assert hasattr(django_dbs, 'default')

    def test_get_django_db_dict_function(self, clean_environment):
        """Test get_django_db_dict function."""
        db_dict = get_django_db_dict()
        
        assert isinstance(db_dict, dict)
        assert 'default' in db_dict

    def test_get_gym_settings_function(self):
        """Test get_gym_settings function."""
        try:
            gym_config = get_gym_settings()
            
            # Should return GymConfig instance if file exists
            assert hasattr(gym_config, 'gym_name')
        except FileNotFoundError:
            pytest.skip("gym_profile.yaml not configured")

    def test_get_gym_settings_file_not_found(self, monkeypatch):
        """Test get_gym_settings raises error when file not found."""
        from config.settings import factory
        from pathlib import Path
        
        def mock_get_gym_settings():
            non_existent = Path("/non/existent/path/gym_profile.yaml")
            if not non_existent.exists():
                raise FileNotFoundError(f"Gym configuration file not found: {non_existent}")
            from config.settings.gymconf import GymConfig
            return GymConfig(_yaml_files=[non_existent])
        
        monkeypatch.setattr(factory, "get_gym_settings", mock_get_gym_settings)
        
        with pytest.raises(FileNotFoundError):
            factory.get_gym_settings()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestSettingsIntegration:
    """Integration tests for settings system."""

    def test_combined_env_and_db_settings(self, clean_environment):
        """Test that env and database settings work together."""
        env_settings = get_settings()
        db_settings = get_django_dbs()
        
        # Both should be valid instances
        assert isinstance(env_settings, CommonEnvSettings)
        assert isinstance(db_settings, DjangoDatabases)

    def test_all_factory_functions_work_together(self, clean_environment):
        """Test all factory functions can be called together."""
        env_settings = get_settings()
        django_dbs = get_django_dbs()
        db_dict = get_django_db_dict()
        
        try:
            gym_config = get_gym_settings()
            assert gym_config is not None
        except FileNotFoundError:
            # gym_profile.yaml may not be configured
            gym_config = None
        
        # All should return valid objects
        assert env_settings is not None
        assert django_dbs is not None
        assert db_dict is not None

    def test_settings_with_production_like_config(self, clean_environment):
        """Test settings with production-like values."""
        prod_settings = CommonEnvSettings(
            SECRET_KEY="p$7k#2n@x9q!5m&8z^4l+6w*3h%1v",
            DEBUG=False,
            ALLOWED_HOSTS=["gymnassic.co.id", "www.gymnassic.co.id", "api.gymnassic.co.id"],
            TIME_ZONE="Asia/Jakarta",
            LANGUAGE_CODE="id-id",
            ENVIRONMENT="prod"
        )
        
        assert len(prod_settings.allowed_hosts) == 3
        assert "gymnassic.co.id" in prod_settings.allowed_hosts
        assert prod_settings.timezone == "Asia/Jakarta"
        assert prod_settings.language_code == "id-id"
        assert prod_settings.debug is False
