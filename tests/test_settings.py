"""
Test suite for environment settings and configuration.

Tests cover:
- CommonSettings validation and loading
- DevelopmentSettings configuration
- ProductionSettings configuration
- EnvironmentFactory behavior
- Database URL parsing
- Settings factory functions
"""

import os
import pytest
from pydantic import ValidationError

from config.settings.envcommon import CommonSettings, DevelopmentSettings, ProductionSettings
from config.settings.factory import EnvironmentFactory, get_settings, load_environment
from config.settings.databases import parse_database_url, get_database_config


# ============================================================================
# COMMON SETTINGS TESTS
# ============================================================================

class TestCommonSettings:
    """Test CommonSettings base configuration."""

    def test_default_common_settings(self, clean_environment):
        """Test CommonSettings with default values."""
        settings = CommonSettings()

        assert settings.secret_key == "django-insecure-default-key-change-this"
        assert settings.debug is False
        assert settings.allowed_hosts == "localhost,127.0.0.1"
        assert settings.environment == "development"
        assert settings.database_url == "sqlite:///db.sqlite3"
        assert settings.database_name is None
        assert settings.log_level == "INFO"
        assert settings.timezone == "UTC"
        assert settings.language_code == "en-us"

    def test_custom_common_settings(self, clean_environment, development_env_data):
        """Test CommonSettings with custom values."""
        settings = CommonSettings(**development_env_data)

        assert settings.secret_key == "dev-secret-key-for-testing"
        assert settings.debug is True
        assert settings.allowed_hosts == "localhost,127.0.0.1"
        assert settings.environment == "development"
        assert settings.database_url == "sqlite:///dev_db.sqlite3"
        assert settings.log_level == "DEBUG"

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

    def test_validate_log_level_valid(self, clean_environment):
        """Test log_level validation with valid values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            settings = CommonSettings(log_level=level)
            assert settings.log_level == level

    def test_validate_log_level_case_insensitive(self, clean_environment):
        """Test log_level validation is case-insensitive."""
        settings = CommonSettings(log_level="debug")
        assert settings.log_level == "DEBUG"

        settings = CommonSettings(log_level="InFo")
        assert settings.log_level == "INFO"

    def test_validate_log_level_invalid(self, clean_environment):
        """Test log_level validation with invalid value."""
        with pytest.raises(ValidationError) as exc_info:
            CommonSettings(log_level="INVALID")
        
        assert "log_level must be one of" in str(exc_info.value)

    def test_validate_environment_valid(self, clean_environment):
        """Test environment validation with valid values."""
        dev_settings = CommonSettings(environment="development")
        assert dev_settings.environment == "development"
        
        prod_settings = CommonSettings(environment="production")
        assert prod_settings.environment == "production"

    def test_validate_environment_case_insensitive(self, clean_environment):
        """Test environment validation is case-insensitive."""
        settings = CommonSettings(environment="DEVELOPMENT")
        assert settings.environment == "development"
        
        settings = CommonSettings(environment="Production")
        assert settings.environment == "production"

    def test_validate_environment_invalid(self, clean_environment):
        """Test environment validation with invalid value."""
        with pytest.raises(ValidationError) as exc_info:
            CommonSettings(environment="staging")
        
        assert "environment must be one of" in str(exc_info.value)


# ============================================================================
# DEVELOPMENT SETTINGS TESTS
# ============================================================================

class TestDevelopmentSettings:
    """Test DevelopmentSettings configuration."""

    def test_development_defaults(self, clean_environment):
        """Test DevelopmentSettings with default values."""
        settings = DevelopmentSettings()
        
        assert settings.debug is True
        assert settings.environment == "development"
        assert settings.log_level == "DEBUG"

    def test_development_custom_values(self, clean_environment):
        """Test DevelopmentSettings with custom values."""
        settings = DevelopmentSettings(
            secret_key="custom-dev-key",
            database_url="sqlite:///custom_dev.db",
            timezone="Asia/Jakarta"
        )
        
        assert settings.secret_key == "custom-dev-key"
        assert settings.database_url == "sqlite:///custom_dev.db"
        assert settings.timezone == "Asia/Jakarta"
        assert settings.debug is True  # Still true by default


# ============================================================================
# PRODUCTION SETTINGS TESTS
# ============================================================================

class TestProductionSettings:
    """Test ProductionSettings configuration."""

    def test_production_defaults(self, clean_environment):
        """Test ProductionSettings with default values (should require explicit config)."""
        settings = ProductionSettings()
        
        # Production should NOT have debug enabled by default
        assert settings.debug is False
        assert settings.environment == "production"

    def test_production_custom_values(self, clean_environment, production_env_data):
        """Test ProductionSettings with production-like values."""
        settings = ProductionSettings(**production_env_data)
        
        assert settings.secret_key != "django-insecure-default-key-change-in-production"
        assert settings.debug is False
        assert settings.environment == "production"
        assert settings.log_level == "WARNING"
        assert "postgresql://" in settings.database_url

    def test_production_requires_secure_secret_key(self, clean_environment):
        """Test that production should use a secure secret key."""
        settings = ProductionSettings(
            secret_key="very-secure-random-key-for-production-use"
        )
        
        # Ensure it's not the default insecure key
        assert "insecure" not in settings.secret_key.lower()


# ============================================================================
# ENVIRONMENT FACTORY TESTS
# ============================================================================

class TestEnvironmentFactory:
    """Test EnvironmentFactory for managing environment configurations."""

    def teardown_method(self):
        """Clean up after each test."""
        EnvironmentFactory.detach()

    def test_attach_development_by_default(self, clean_environment):
        """Test factory attaches development environment by default."""
        settings = EnvironmentFactory.attach()
        
        assert isinstance(settings, DevelopmentSettings)
        assert settings.debug is True
        assert EnvironmentFactory.is_attached()
        assert EnvironmentFactory.current_type() == "development"

    def test_attach_production_explicitly(self, clean_environment):
        """Test factory attaches production environment when specified."""
        settings = EnvironmentFactory.attach("production")
        
        assert isinstance(settings, ProductionSettings)
        assert settings.debug is False
        assert EnvironmentFactory.current_type() == "production"

    def test_attach_from_environment_variable(self, clean_environment):
        """Test factory reads environment type from env variable."""
        os.environ["__COMMON_ENVIRONMENT"] = "production"
        settings = EnvironmentFactory.attach()
        
        assert isinstance(settings, ProductionSettings)
        assert EnvironmentFactory.current_type() == "production"

    def test_attach_invalid_environment(self, clean_environment):
        """Test factory raises error for invalid environment type."""
        with pytest.raises(ValueError) as exc_info:
            EnvironmentFactory.attach("staging")
        
        assert "Invalid environment type" in str(exc_info.value)

    def test_current_without_attach_raises_error(self, clean_environment):
        """Test accessing current settings without attach raises error."""
        with pytest.raises(RuntimeError) as exc_info:
            EnvironmentFactory.current()
        
        assert "No environment attached" in str(exc_info.value)

    def test_current_after_attach_returns_settings(self, clean_environment):
        """Test current() returns settings after attach."""
        EnvironmentFactory.attach("development")
        settings = EnvironmentFactory.current()
        
        assert isinstance(settings, DevelopmentSettings)

    def test_get_or_attach_when_not_attached(self, clean_environment):
        """Test get_or_attach attaches when not already attached."""
        assert not EnvironmentFactory.is_attached()
        
        settings = EnvironmentFactory.get_or_attach()
        
        assert EnvironmentFactory.is_attached()
        assert isinstance(settings, CommonSettings)

    def test_get_or_attach_when_already_attached(self, clean_environment):
        """Test get_or_attach returns existing when already attached."""
        first = EnvironmentFactory.attach("development")
        second = EnvironmentFactory.get_or_attach("production")
        
        # Should return the first attached, not create a new one
        assert first is second

    def test_detach_clears_environment(self, clean_environment):
        """Test detach clears the current environment."""
        EnvironmentFactory.attach("development")
        assert EnvironmentFactory.is_attached()
        
        EnvironmentFactory.detach()
        
        assert not EnvironmentFactory.is_attached()
        assert EnvironmentFactory.current_type() is None

    def test_reload_with_same_environment(self, clean_environment):
        """Test reload recreates settings with same environment type."""
        EnvironmentFactory.attach("development")
        original_type = EnvironmentFactory.current_type()
        
        reloaded = EnvironmentFactory.reload()
        
        assert EnvironmentFactory.current_type() == original_type
        assert isinstance(reloaded, DevelopmentSettings)

    def test_reload_without_attach_raises_error(self, clean_environment):
        """Test reload without attach raises error."""
        with pytest.raises(RuntimeError) as exc_info:
            EnvironmentFactory.reload()
        
        assert "No environment to reload" in str(exc_info.value)


# ============================================================================
# DATABASE URL PARSING TESTS
# ============================================================================

class TestDatabaseURLParsing:
    """Test database URL parsing functionality."""

    def test_parse_sqlite_relative_path(self):
        """Test parsing SQLite with relative path."""
        config = parse_database_url("sqlite:///db.sqlite3")
        
        assert config["ENGINE"] == "django.db.backends.sqlite3"
        assert config["NAME"] == "db.sqlite3"

    def test_parse_sqlite_absolute_path(self):
        """Test parsing SQLite with absolute path."""
        config = parse_database_url("sqlite:////absolute/path/to/db.sqlite3")
        
        assert config["ENGINE"] == "django.db.backends.sqlite3"
        assert config["NAME"] == "/absolute/path/to/db.sqlite3"

    def test_parse_sqlite_memory(self):
        """Test parsing SQLite in-memory database."""
        config = parse_database_url("sqlite:///:memory:")
        
        assert config["ENGINE"] == "django.db.backends.sqlite3"
        assert config["NAME"] == ":memory:"

    def test_parse_postgresql_full(self):
        """Test parsing PostgreSQL URL with full credentials."""
        config = parse_database_url("postgresql://myuser:mypass@localhost:5432/mydb")
        
        assert config["ENGINE"] == "django.db.backends.postgresql"
        assert config["NAME"] == "mydb"
        assert config["USER"] == "myuser"
        assert config["PASSWORD"] == "mypass"
        assert config["HOST"] == "localhost"
        assert config["PORT"] == 5432

    def test_parse_postgresql_minimal(self):
        """Test parsing PostgreSQL URL with minimal info."""
        config = parse_database_url("postgresql://localhost/testdb")
        
        assert config["ENGINE"] == "django.db.backends.postgresql"
        assert config["NAME"] == "testdb"
        assert config["HOST"] == "localhost"
        assert config["USER"] == ""
        assert config["PASSWORD"] == ""

    def test_parse_postgres_alias(self):
        """Test parsing with 'postgres' scheme (alias for postgresql)."""
        config = parse_database_url("postgres://user:pass@host:5432/db")
        
        assert config["ENGINE"] == "django.db.backends.postgresql"
        assert config["NAME"] == "db"

    def test_parse_unknown_scheme_defaults_to_sqlite(self):
        """Test unknown scheme defaults to SQLite."""
        config = parse_database_url("unknown:///path/to/db")
        
        assert config["ENGINE"] == "django.db.backends.sqlite3"


class TestGetDatabaseConfig:
    """Test get_database_config function."""

    def test_get_database_config_default(self, clean_environment):
        """Test getting database config with default settings."""
        os.environ["__COMMON_DATABASE_URL"] = "sqlite:///test.db"
        
        EnvironmentFactory.detach()  # Ensure clean state
        config = get_database_config()
        
        assert "default" in config
        assert config["default"]["ENGINE"] == "django.db.backends.sqlite3"

    def test_get_database_config_with_override_name(self, clean_environment):
        """Test database config with explicit database name override."""
        os.environ["__COMMON_DATABASE_URL"] = "sqlite:///default.db"
        os.environ["__COMMON_DATABASE_NAME"] = "custom_name.db"
        
        EnvironmentFactory.detach()
        config = get_database_config()
        
        assert config["default"]["NAME"] == "custom_name.db"


# ============================================================================
# FACTORY FUNCTIONS TESTS
# ============================================================================

class TestFactoryFunctions:
    """Test module-level factory functions."""

    def teardown_method(self):
        """Clean up after each test."""
        EnvironmentFactory.detach()

    def test_get_settings_function(self, clean_environment):
        """Test get_settings convenience function."""
        settings = get_settings()
        
        assert isinstance(settings, CommonSettings)
        assert EnvironmentFactory.is_attached()

    def test_load_environment_development(self, clean_environment):
        """Test load_environment function for development."""
        settings = load_environment("development")
        
        assert isinstance(settings, DevelopmentSettings)

    def test_load_environment_production(self, clean_environment):
        """Test load_environment function for production."""
        settings = load_environment("production")
        
        assert isinstance(settings, ProductionSettings)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
class TestSettingsIntegration:
    """Integration tests for settings system."""

    def test_full_settings_lifecycle(self, clean_environment):
        """Test complete lifecycle: load, use, reload, detach."""
        # Load development
        dev_settings = load_environment("development")
        assert dev_settings.debug is True
        
        # Use settings
        current = get_settings()
        assert current.debug is True
        
        # Detach
        EnvironmentFactory.detach()
        assert not EnvironmentFactory.is_attached()
        
        # Re-attach with production
        prod_settings = EnvironmentFactory.attach("production")
        assert prod_settings.debug is False

    def test_settings_with_real_world_production_config(self, clean_environment):
        """Test production configuration with realistic values."""
        prod_settings = ProductionSettings(
            secret_key="p$7k#2n@x9q!5m&8z^4l+6w*3h%1v",
            debug=False,
            allowed_hosts="gymnassic.co.id,www.gymnassic.co.id,api.gymnassic.co.id",
            database_url="postgresql://gym_user:secure_password@db.gymnassic.local:5432/gymnassic_prod",
            database_name="gymnassic_prod",
            log_level="ERROR",
            timezone="Asia/Jakarta",
            language_code="id-id",
        )
        
        hosts = prod_settings.get_allowed_hosts_list()
        assert len(hosts) == 3
        assert "gymnassic.co.id" in hosts
        assert prod_settings.timezone == "Asia/Jakarta"
        assert prod_settings.language_code == "id-id"
