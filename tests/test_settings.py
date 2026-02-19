"""
Test suite for environment settings and configuration.

Tests cover:
- __COMMON base settings validation and loading
- LocalSettings configuration
- ProductionSettings configuration
- Settings factory functions
- Database settings configuration
- Settings singleton behavior
"""

import os
import pytest
from pydantic import ValidationError

from config.settings.envcommon import (
    __COMMON as CommonSettings,
    LocalSettings,
    ProductionSettings,
    get_settings_instance,
)
from config.settings.databases import (
    DatabaseSettings,
    LocalDatabaseSettings,
    ProductionDatabaseSettings,
    get_database_settings_instance,
)
from config.settings.factory import (
    get_settings,
    get_database_settings,
    get_gym_settings,
    override_settings,
    reset_settings,
)


# ============================================================================
# COMMON SETTINGS TESTS
# ============================================================================

class TestCommonSettings:
    """Test __COMMON base configuration."""

    def test_default_common_settings(self, clean_environment):
        """Test __COMMON with default values."""
        settings = CommonSettings()

        assert settings.secret_key == "django-insecure-change-me-in-production"
        assert settings.debug is True
        assert settings.allowed_hosts == "localhost,127.0.0.1"
        assert settings.environment == "local"
        assert settings.timezone == "Asia/Jakarta"
        assert settings.language_code == "en-us"

    def test_custom_common_settings(self, clean_environment, local_env_data):
        """Test __COMMON with custom values."""
        settings = CommonSettings(**local_env_data)

        assert settings.secret_key == "local-secret-key-for-testing"
        assert settings.debug is True
        assert settings.allowed_hosts == "localhost,127.0.0.1,0.0.0.0"
        assert settings.environment == "local"

    def test_get_allowed_hosts_list(self, clean_environment):
        """Test conversion of allowed_hosts string to list."""
        settings = CommonSettings(allowed_hosts="localhost,127.0.0.1,example.com")
        hosts = settings.get_allowed_hosts_list()

        assert isinstance(hosts, list)
        assert len(hosts) == 3
        assert "localhost" in hosts
        assert "127.0.0.1" in hosts
        assert "example.com" in hosts

    def test_get_allowed_hosts_list_with_spaces(self, clean_environment):
        """Test allowed_hosts parsing with extra spaces."""
        settings = CommonSettings(allowed_hosts="localhost, 127.0.0.1 , example.com")
        hosts = settings.get_allowed_hosts_list()

        assert len(hosts) == 3
        assert all(host.strip() == host for host in hosts)  # No extra spaces

    def test_validate_environment_valid(self, clean_environment):
        """Test environment validation with valid values."""
        local_settings = CommonSettings(environment="local")
        assert local_settings.environment == "local"
        
        prod_settings = CommonSettings(
            environment="production",
            secret_key="secure-production-key-for-testing-purposes"
        )
        assert prod_settings.environment == "production"

    def test_validate_environment_invalid(self, clean_environment):
        """Test environment validation with invalid value."""
        with pytest.raises(ValidationError) as exc_info:
            CommonSettings(environment="staging")
        
        assert "Invalid environment" in str(exc_info.value)

    def test_is_local_method(self, clean_environment):
        """Test is_local() method."""
        local_settings = CommonSettings(environment="local")
        assert local_settings.is_local() is True
        assert local_settings.is_production() is False

    def test_is_production_method(self, clean_environment):
        """Test is_production() method."""
        prod_settings = CommonSettings(
            environment="production",
            secret_key="secure-production-key-for-testing-purposes"
        )
        assert prod_settings.is_production() is True
        assert prod_settings.is_local() is False


# ============================================================================
# LOCAL SETTINGS TESTS
# ============================================================================

class TestLocalSettings:
    """Test LocalSettings configuration."""

    def test_local_defaults(self, clean_environment):
        """Test LocalSettings with default values."""
        settings = LocalSettings()
        
        assert settings.debug is True
        assert settings.environment == "local"
        assert settings.allowed_hosts == "localhost,127.0.0.1,0.0.0.0"

    def test_local_custom_values(self, clean_environment):
        """Test LocalSettings with custom values."""
        settings = LocalSettings(
            secret_key="custom-local-key",
            timezone="Asia/Jakarta"
        )
        
        assert settings.secret_key == "custom-local-key"
        assert settings.timezone == "Asia/Jakarta"
        assert settings.debug is True  # Still true by default


# ============================================================================
# PRODUCTION SETTINGS TESTS
# ============================================================================

class TestProductionSettings:
    """Test ProductionSettings configuration."""

    def test_production_defaults(self, clean_environment):
        """Test ProductionSettings requires explicit secret_key."""
        # Production requires secret_key to be set
        with pytest.raises(ValidationError):
            ProductionSettings()

    def test_production_custom_values(self, clean_environment, production_env_data):
        """Test ProductionSettings with production-like values."""
        settings = ProductionSettings(**production_env_data)
        
        assert settings.secret_key != "django-insecure-change-me-in-production"
        assert settings.debug is False
        assert settings.environment == "production"

    def test_production_requires_secure_secret_key(self, clean_environment):
        """Test that production enforces secure secret key."""
        with pytest.raises(ValidationError) as exc_info:
            ProductionSettings(
                secret_key="django-insecure-change-me-in-production"
            )
        
        assert "You must set a secure SECRET_KEY" in str(exc_info.value)

    def test_production_valid_secret_key(self, clean_environment):
        """Test production with a valid secure secret key."""
        settings = ProductionSettings(
            secret_key="very-secure-random-key-for-production-use-12345"
        )
        
        assert settings.secret_key == "very-secure-random-key-for-production-use-12345"
        assert settings.debug is False
        assert settings.environment == "production"


# ============================================================================
# DATABASE SETTINGS TESTS
# ============================================================================

class TestDatabaseSettings:
    """Test DatabaseSettings configuration."""

    def test_default_database_settings(self, clean_environment):
        """Test DatabaseSettings with default values."""
        settings = DatabaseSettings()

        assert settings.environment == "local"
        assert settings.database_engine == "django.db.backends.sqlite3"
        assert "db.sqlite3" in settings.database_name

    def test_database_config_sqlite(self, clean_environment, local_db_data):
        """Test database configuration for SQLite."""
        settings = DatabaseSettings(**local_db_data)
        config = settings.get_database_config()

        assert config["ENGINE"] == "django.db.backends.sqlite3"
        assert config["NAME"] == "db.sqlite3"
        assert "USER" not in config  # SQLite doesn't need user

    def test_database_config_postgresql(self, clean_environment, production_db_data):
        """Test database configuration for PostgreSQL."""
        settings = DatabaseSettings(**production_db_data)
        config = settings.get_database_config()

        assert config["ENGINE"] == "django.db.backends.postgresql"
        assert config["NAME"] == "gymnassic_prod"
        assert config["USER"] == "dbuser"
        assert config["PASSWORD"] == "dbpass123"
        assert config["HOST"] == "localhost"
        assert config["PORT"] == "5432"
        assert config["CONN_MAX_AGE"] == 600
        assert config["CONN_HEALTH_CHECKS"] is True

    def test_is_sqlite_method(self, clean_environment):
        """Test is_sqlite() method."""
        sqlite_settings = DatabaseSettings(database_engine="django.db.backends.sqlite3")
        assert sqlite_settings.is_sqlite() is True

    def test_is_postgresql_method(self, clean_environment):
        """Test is_postgresql() method."""
        pg_settings = DatabaseSettings(database_engine="django.db.backends.postgresql")
        assert pg_settings.is_postgresql() is True

    def test_is_mysql_method(self, clean_environment):
        """Test is_mysql() method."""
        mysql_settings = DatabaseSettings(database_engine="django.db.backends.mysql")
        assert mysql_settings.is_mysql() is True


class TestLocalDatabaseSettings:
    """Test LocalDatabaseSettings configuration."""

    def test_local_database_defaults(self, clean_environment):
        """Test LocalDatabaseSettings with default values."""
        settings = LocalDatabaseSettings()

        assert settings.environment == "local"
        assert settings.database_engine == "django.db.backends.sqlite3"
        assert "db.sqlite3" in settings.database_name


class TestProductionDatabaseSettings:
    """Test ProductionDatabaseSettings configuration."""

    def test_production_database_requires_config(self, clean_environment):
        """Test ProductionDatabaseSettings requires explicit configuration."""
        # Production requires database_name, database_user, database_password
        with pytest.raises(ValidationError):
            ProductionDatabaseSettings()

    def test_production_database_valid_config(self, clean_environment):
        """Test ProductionDatabaseSettings with valid configuration."""
        settings = ProductionDatabaseSettings(
            database_name="gymnassic_prod",
            database_user="dbuser",
            database_password="securepass123"
        )

        assert settings.environment == "production"
        assert settings.database_engine == "django.db.backends.postgresql"
        assert settings.database_conn_max_age == 600
        assert settings.database_conn_health_checks is True


# ============================================================================
# FACTORY FUNCTIONS TESTS
# ============================================================================

class TestFactoryFunctions:
    """Test settings factory functions."""

    def test_get_settings_function(self, clean_environment):
        """Test get_settings convenience function."""
        settings = get_settings()
        
        assert isinstance(settings, CommonSettings)

    def test_get_database_settings_function(self, clean_environment):
        """Test get_database_settings function."""
        db_settings = get_database_settings()
        
        assert isinstance(db_settings, DatabaseSettings)

    def test_get_gym_settings_function(self, clean_environment):
        """Test get_gym_settings function (may return None if not configured)."""
        gym_config = get_gym_settings()
        
        # Should return None if gym_profile.yaml doesn't exist or has errors
        # Otherwise returns GymProfile instance
        assert gym_config is None or hasattr(gym_config, 'gym_name')

    def test_override_settings_function(self, clean_environment):
        """Test override_settings function for testing."""
        # Create custom settings
        custom_settings = LocalSettings(secret_key="test-override-key")
        
        # Override
        override_settings(custom_settings)
        
        # Get settings should return overridden
        current = get_settings()
        assert current.secret_key == "test-override-key"
        
        # Reset
        reset_settings()

    def test_reset_settings_function(self, clean_environment):
        """Test reset_settings function."""
        # Override first
        custom_settings = LocalSettings(secret_key="test-key")
        override_settings(custom_settings)
        
        # Reset
        reset_settings()
        
        # Settings should be back to default
        current = get_settings()
        # After reset, should create new instance with defaults
        assert isinstance(current, CommonSettings)


# ============================================================================
# SINGLETON BEHAVIOR TESTS
# ============================================================================

class TestSingletonBehavior:
    """Test singleton behavior of settings instances."""

    def test_get_settings_instance_returns_same_object(self, clean_environment):
        """Test get_settings_instance returns the same object."""
        first = get_settings()
        second = get_settings()
        
        # Should be the same object (singleton)
        assert first is second

    def test_get_database_settings_instance_returns_same_object(self, clean_environment):
        """Test get_database_settings_instance returns same object."""
        first = get_database_settings()
        second = get_database_settings()
        
        # Should be the same object (singleton)
        assert first is second


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestSettingsIntegration:
    """Integration tests for settings system."""

    def test_settings_with_real_world_production_config(self, clean_environment):
        """Test production configuration with realistic values."""
        prod_settings = ProductionSettings(
            secret_key="p$7k#2n@x9q!5m&8z^4l+6w*3h%1v",
            debug=False,
            allowed_hosts="gymnassic.co.id,www.gymnassic.co.id,api.gymnassic.co.id",
            timezone="Asia/Jakarta",
            language_code="id-id",
        )
        
        hosts = prod_settings.get_allowed_hosts_list()
        assert len(hosts) == 3
        assert "gymnassic.co.id" in hosts
        assert prod_settings.timezone == "Asia/Jakarta"
        assert prod_settings.language_code == "id-id"

    def test_combined_env_and_db_settings(self, clean_environment):
        """Test that env and database settings work together."""
        env_settings = get_settings()
        db_settings = get_database_settings()
        
        # Both should be valid instances
        assert isinstance(env_settings, CommonSettings)
        assert isinstance(db_settings, DatabaseSettings)
        
        # Environment should match
        assert env_settings.environment == db_settings.environment
