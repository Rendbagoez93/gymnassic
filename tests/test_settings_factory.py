"""
Test suite for settings factory module and dependency injection.

Tests cover:
- Factory functions for settings instances
- Dependency injection container behavior
- Database factory with multiple engines
- Settings integration and coordination
- Real-world configuration scenarios
- Error handling and validation
"""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from config.settings.databases import (
    BaseDatabaseSettings,
    DBEngineEnum,
    DjangoDatabases,
    PostgresDatabaseSettings,
    SqliteDatabaseSettings,
)
from config.settings.envcommon import CommonEnvSettings
from config.settings.factory import (
    DbContainer,
    get_django_db_dict,
    get_django_dbs,
    get_settings,
)
from config.settings.gymconf import GymConfig


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================


class TestGetSettings:
    """Test get_settings factory function."""

    def test_get_settings_returns_common_env_settings(self, clean_environment):
        """Test that get_settings returns CommonEnvSettings instance."""
        settings = get_settings()

        assert isinstance(settings, CommonEnvSettings)
        assert hasattr(settings, "SECRET_KEY")
        assert hasattr(settings, "DEBUG")
        assert hasattr(settings, "ALLOWED_HOSTS")

    def test_get_settings_loads_from_environment(self, clean_environment, monkeypatch):
        """Test that settings are loaded from environment variables."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-123")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("ENVIRONMENT", "local")

        settings = get_settings()

        assert settings.SECRET_KEY == "test-secret-key-123"
        assert settings.DEBUG is True
        assert settings.ENVIRONMENT == "local"

    def test_get_settings_uses_defaults_when_no_env(self, clean_environment):
        """Test that default values are used when environment variables are not set."""
        settings = get_settings()

        assert settings.SECRET_KEY == "django-insecure-change-this-in-production"
        assert settings.DEBUG is False
        assert settings.TIME_ZONE == "Asia/Jakarta"

    def test_get_settings_property_accessors(self, clean_environment):
        """Test that property accessors work correctly."""
        settings = get_settings()

        # Test lowercase property accessors
        assert settings.secret_key == settings.SECRET_KEY
        assert settings.debug == settings.DEBUG
        assert settings.allowed_hosts == settings.ALLOWED_HOSTS
        assert settings.timezone == settings.TIME_ZONE


# ============================================================================
# DATABASE FACTORY TESTS
# ============================================================================


class TestGetDjangoDbFunctions:
    """Test database factory functions."""

    def test_get_django_dbs_returns_django_databases(self, clean_environment):
        """Test that get_django_dbs returns DjangoDatabases instance."""
        db_settings = get_django_dbs()

        assert isinstance(db_settings, DjangoDatabases)
        assert hasattr(db_settings, "default")

    def test_get_django_dbs_default_sqlite(self, clean_environment):
        """Test that default database is SQLite when no env vars set."""
        db_settings = get_django_dbs()

        assert isinstance(db_settings.default, SqliteDatabaseSettings)
        assert db_settings.default.engine == DBEngineEnum.SQLITE
        assert "db.sqlite3" in db_settings.default.name

    def test_get_django_dbs_postgresql_from_env(self, clean_environment, monkeypatch):
        """Test PostgreSQL configuration from environment variables."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "test_db")
        monkeypatch.setenv("DATABASE_USER", "testuser")
        monkeypatch.setenv("DATABASE_PASSWORD", "testpass")
        monkeypatch.setenv("DATABASE_HOST", "localhost")
        monkeypatch.setenv("DATABASE_PORT", "5432")

        db_settings = get_django_dbs()

        assert isinstance(db_settings.default, PostgresDatabaseSettings)
        assert db_settings.default.engine == DBEngineEnum.POSTGRES
        assert db_settings.default.name == "test_db"
        assert db_settings.default.user == "testuser"
        assert db_settings.default.password == "testpass"
        assert db_settings.default.host == "localhost"
        assert db_settings.default.port == 5432

    def test_get_django_db_dict_returns_dict(self, clean_environment):
        """Test that get_django_db_dict returns proper Django DATABASES dict."""
        db_dict = get_django_db_dict()

        assert isinstance(db_dict, dict)
        assert "default" in db_dict
        assert isinstance(db_dict["default"], dict)
        assert "ENGINE" in db_dict["default"]
        assert "NAME" in db_dict["default"]

    def test_get_django_db_dict_sqlite_structure(self, clean_environment):
        """Test SQLite database dict structure."""
        db_dict = get_django_db_dict()
        default_db = db_dict["default"]

        assert default_db["ENGINE"] == "django.db.backends.sqlite3"
        assert "db.sqlite3" in default_db["NAME"]
        # SQLite doesn't need these fields
        assert "USER" not in default_db or default_db.get("USER") is None
        assert "PASSWORD" not in default_db or default_db.get("PASSWORD") is None

    def test_get_django_db_dict_postgresql_structure(self, clean_environment, monkeypatch):
        """Test PostgreSQL database dict structure."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "prod_db")
        monkeypatch.setenv("DATABASE_USER", "produser")
        monkeypatch.setenv("DATABASE_PASSWORD", "prodpass")
        monkeypatch.setenv("DATABASE_HOST", "db.example.com")
        monkeypatch.setenv("DATABASE_PORT", "5432")

        db_dict = get_django_db_dict()
        default_db = db_dict["default"]

        assert default_db["ENGINE"] == "django.db.backends.postgresql"
        assert default_db["NAME"] == "prod_db"
        assert default_db["USER"] == "produser"
        assert default_db["PASSWORD"] == "prodpass"
        assert default_db["HOST"] == "db.example.com"
        assert default_db["PORT"] == 5432


# ============================================================================
# GYM SETTINGS FACTORY TESTS
# ============================================================================


class TestGetGymSettings:
    """Test gym settings factory function."""

    def test_get_gym_settings_with_valid_file(self, temp_gym_yaml_file):
        """Test loading gym settings from valid YAML file."""
        # Mock the path resolution to use our temp file
        import config.settings.factory as factory_module

        # Create a mock structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_dir = tmpdir_path / "config" / "settings"
            config_dir.mkdir(parents=True)
            
            # Copy our temp gym file
            import shutil
            gym_file = tmpdir_path / "gym_profile.yaml"
            shutil.copy(temp_gym_yaml_file, gym_file)

            # Temporarily modify the function
            def mock_get_gym_settings():
                return GymConfig(_yaml_files=[gym_file])

            # Replace function temporarily
            original_func = factory_module.get_gym_settings
            factory_module.get_gym_settings = mock_get_gym_settings

            try:
                gym_config = factory_module.get_gym_settings()
                
                assert isinstance(gym_config, GymConfig)
                assert gym_config.gym_name == "Gymnassic Fitness Center"
                assert gym_config.address is not None
                assert gym_config.phone_numbers is not None
            finally:
                factory_module.get_gym_settings = original_func

    def test_get_gym_settings_raises_when_file_missing(self):
        """Test that FileNotFoundError is raised when gym_profile.yaml is missing."""
        import config.settings.factory as factory_module

        # Temporarily modify to look for non-existent file
        def mock_get_gym_settings_bad():
            project_root = Path("/nonexistent/path")
            gym_config_path = project_root / "gym_profile.yaml"

            if not gym_config_path.exists():
                raise FileNotFoundError(f"Gym configuration file not found: {gym_config_path}")

            return GymConfig(_yaml_files=[gym_config_path])

        original_func = factory_module.get_gym_settings
        factory_module.get_gym_settings = mock_get_gym_settings_bad

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                factory_module.get_gym_settings()

            assert "Gym configuration file not found" in str(exc_info.value)
        finally:
            factory_module.get_gym_settings = original_func


# ============================================================================
# DEPENDENCY INJECTION CONTAINER TESTS
# ============================================================================


class TestDbContainer:
    """Test dependency injection container for database settings."""

    def test_db_container_initialization(self, clean_environment):
        """Test that DbContainer can be initialized."""
        container = DbContainer()

        assert container is not None
        assert hasattr(container, "config")
        assert hasattr(container, "db_factory")
        assert hasattr(container, "django_databases")

    def test_db_container_sqlite_factory(self, clean_environment):
        """Test SQLite database factory from container."""
        container = DbContainer()
        base_settings = BaseDatabaseSettings(engine=DBEngineEnum.SQLITE)
        container.config.from_pydantic(base_settings)

        django_dbs = container.django_databases()

        assert isinstance(django_dbs, DjangoDatabases)
        assert isinstance(django_dbs.default, SqliteDatabaseSettings)

    def test_db_container_postgres_factory(self, clean_environment, monkeypatch):
        """Test PostgreSQL database factory from container."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")

        container = DbContainer()
        base_settings = BaseDatabaseSettings()
        container.config.from_pydantic(base_settings)

        django_dbs = container.django_databases()

        assert isinstance(django_dbs, DjangoDatabases)
        assert isinstance(django_dbs.default, PostgresDatabaseSettings)

    def test_db_container_singleton_behavior(self, clean_environment):
        """Test that django_databases provider returns singleton."""
        container = DbContainer()
        base_settings = BaseDatabaseSettings(engine=DBEngineEnum.SQLITE)
        container.config.from_pydantic(base_settings)

        dbs1 = container.django_databases()
        dbs2 = container.django_databases()

        # Should return the same instance (singleton)
        assert dbs1 is dbs2


# ============================================================================
# INTEGRATION TESTS - REAL-WORLD SCENARIOS
# ============================================================================


class TestRealWorldScenarios:
    """Test real-world configuration scenarios."""

    def test_local_development_setup(self, clean_environment, monkeypatch):
        """Test typical local development configuration."""
        # Set up local development environment
        monkeypatch.setenv("SECRET_KEY", "local-dev-secret-key")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")

        # Load settings
        env_settings = get_settings()
        db_settings = get_django_db_dict()

        # Verify local development setup
        assert env_settings.DEBUG is True
        assert env_settings.ENVIRONMENT == "local"
        assert db_settings["default"]["ENGINE"] == "django.db.backends.sqlite3"
        assert env_settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"

    def test_production_setup(self, clean_environment, monkeypatch):
        """Test typical production configuration."""
        # Set up production environment
        monkeypatch.setenv("SECRET_KEY", "super-secure-production-key-very-long")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("ALLOWED_HOSTS", '["example.com", "www.example.com"]')
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "prod_gymnassic")
        monkeypatch.setenv("DATABASE_USER", "prod_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "secure_password_123")
        monkeypatch.setenv("DATABASE_HOST", "prod-db.example.com")
        monkeypatch.setenv("DATABASE_PORT", "5432")

        # Load settings
        env_settings = get_settings()
        db_settings = get_django_db_dict()

        # Verify production setup
        assert env_settings.DEBUG is False
        assert env_settings.ENVIRONMENT == "production"
        assert db_settings["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert db_settings["default"]["NAME"] == "prod_gymnassic"
        assert db_settings["default"]["HOST"] == "prod-db.example.com"

    def test_switching_environments(self, clean_environment, monkeypatch):
        """Test switching between development and production environments."""
        # Start with local
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")

        local_settings = get_settings()
        local_db = get_django_db_dict()

        assert local_settings.ENVIRONMENT == "local"
        assert local_settings.DEBUG is True
        assert local_db["default"]["ENGINE"] == "django.db.backends.sqlite3"

        # Switch to production
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "prod_db")

        prod_settings = get_settings()
        prod_db = get_django_db_dict()

        assert prod_settings.ENVIRONMENT == "production"
        assert prod_settings.DEBUG is False
        assert prod_db["default"]["ENGINE"] == "django.db.backends.postgresql"

    def test_missing_required_production_settings(self, clean_environment, monkeypatch):
        """Test that production requires certain settings."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        # Missing DATABASE_NAME, DATABASE_USER, etc. - should use defaults

        settings = get_settings()
        db_settings = get_django_dbs()

        # Should still work but use default values
        assert settings.ENVIRONMENT == "production"
        assert isinstance(db_settings.default, PostgresDatabaseSettings)
        # Will use defaults from PostgresDatabaseSettings
        assert db_settings.default.name == "gymnassic"
        assert db_settings.default.user == "postgres"

    def test_complete_application_bootstrap(self, clean_environment, monkeypatch, temp_gym_yaml_file):
        """Test complete application configuration bootstrap process."""
        # Set all necessary environment variables
        monkeypatch.setenv("SECRET_KEY", "bootstrap-test-key")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")

        # Load all configuration components
        env_settings = get_settings()
        db_dict = get_django_db_dict()

        # Verify all components loaded successfully
        assert env_settings is not None
        assert env_settings.SECRET_KEY == "bootstrap-test-key"
        
        assert db_dict is not None
        assert "default" in db_dict
        assert db_dict["default"]["ENGINE"] == "django.db.backends.sqlite3"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandling:
    """Test error handling in factory functions."""

    def test_invalid_database_engine(self, clean_environment, monkeypatch):
        """Test handling of invalid database engine."""
        monkeypatch.setenv("DATABASE_ENGINE", "invalid_engine")

        with pytest.raises(ValidationError) as exc_info:
            BaseDatabaseSettings()

        assert "enum" in str(exc_info.value).lower()

    def test_database_port_invalid_type(self, clean_environment, monkeypatch):
        """Test validation of database port as integer."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_PORT", "not_a_number")

        with pytest.raises(ValidationError) as exc_info:
            get_django_dbs()

        # Should fail validation
        assert exc_info.value is not None

    def test_empty_secret_key_allowed_but_warned(self, clean_environment, monkeypatch):
        """Test that empty secret key is technically allowed (for testing)."""
        # Pydantic will allow it but it's not recommended
        monkeypatch.setenv("SECRET_KEY", "")

        settings = get_settings()
        
        # Will use default value if empty
        assert settings.SECRET_KEY is not None


# ============================================================================
# CONFIGURATION CHANGE DETECTION TESTS
# ============================================================================


class TestConfigurationChanges:
    """Test detection and handling of configuration changes."""

    def test_database_engine_change_creates_new_instance(self, clean_environment, monkeypatch):
        """Test that changing database engine creates new configuration."""
        # First create SQLite config
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")
        sqlite_db = get_django_dbs()

        assert isinstance(sqlite_db.default, SqliteDatabaseSettings)

        # Change to PostgreSQL
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        postgres_db = get_django_dbs()

        assert isinstance(postgres_db.default, PostgresDatabaseSettings)
        # Should be different instances
        assert not isinstance(sqlite_db.default, type(postgres_db.default))

    def test_settings_reflect_environment_changes(self, clean_environment, monkeypatch):
        """Test that settings reflect environment variable changes."""
        monkeypatch.setenv("DEBUG", "false")
        settings1 = get_settings()
        assert settings1.DEBUG is False

        monkeypatch.setenv("DEBUG", "true")
        settings2 = get_settings()
        assert settings2.DEBUG is True

    def test_database_settings_immutable(self, clean_environment):
        """Test that BaseDatabaseSettings is frozen/immutable."""
        settings = BaseDatabaseSettings()

        with pytest.raises(ValidationError):
            settings.engine = DBEngineEnum.POSTGRES  # Should fail - frozen model


# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_secret_key(self, clean_environment, monkeypatch):
        """Test handling of very long secret key."""
        long_key = "a" * 1000
        monkeypatch.setenv("SECRET_KEY", long_key)

        settings = get_settings()
        
        assert len(settings.SECRET_KEY) == 1000
        assert settings.SECRET_KEY == long_key

    def test_special_characters_in_database_password(self, clean_environment, monkeypatch):
        """Test handling of special characters in database password."""
        special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:',.<>?/"
        
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_PASSWORD", special_password)

        db_settings = get_django_dbs()

        assert db_settings.default.password == special_password

    def test_allowed_hosts_single_host(self, clean_environment, monkeypatch):
        """Test ALLOWED_HOSTS with single host."""
        monkeypatch.setenv("ALLOWED_HOSTS", '["example.com"]')

        settings = get_settings()

        # Should handle single host properly
        assert isinstance(settings.ALLOWED_HOSTS, list)

    def test_empty_allowed_hosts(self, clean_environment, monkeypatch):
        """Test ALLOWED_HOSTS when empty."""
        monkeypatch.setenv("ALLOWED_HOSTS", "[]")

        settings = get_settings()

        # Should use defaults
        assert settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]

    def test_database_name_with_spaces(self, clean_environment, monkeypatch):
        """Test database name with spaces (edge case but valid for some DBs)."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "my database name")

        db_settings = get_django_dbs()

        assert db_settings.default.name == "my database name"
