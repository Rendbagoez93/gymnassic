"""
Test suite for database settings and configuration.

Tests cover:
- Database engine enumeration and validation
- SQLite database settings
- PostgreSQL database settings
- Database settings factory patterns
- Environment-based database configuration
- Real-world database migration scenarios
- Connection string validation
"""

import os

import pytest
from pydantic import ValidationError

from config.settings.databases import (
    BaseDatabaseSettings,
    DBEngineEnum,
    DjangoDatabases,
    PostgresDatabaseSettings,
    SqliteDatabaseSettings,
)


# ============================================================================
# DATABASE ENGINE TESTS
# ============================================================================


class TestDBEngineEnum:
    """Test database engine enumeration."""

    def test_sqlite_engine_value(self):
        """Test SQLite engine enum value."""
        assert DBEngineEnum.SQLITE == "django.db.backends.sqlite3"
        assert DBEngineEnum.SQLITE.value == "django.db.backends.sqlite3"
        assert DBEngineEnum.SQLITE.name == "SQLITE"

    def test_postgres_engine_value(self):
        """Test PostgreSQL engine enum value."""
        assert DBEngineEnum.POSTGRES == "django.db.backends.postgresql"
        assert DBEngineEnum.POSTGRES.value == "django.db.backends.postgresql"
        assert DBEngineEnum.POSTGRES.name == "POSTGRES"

    def test_engine_from_name(self):
        """Test creating engine enum from name string."""
        sqlite = DBEngineEnum["SQLITE"]
        postgres = DBEngineEnum["POSTGRES"]

        assert sqlite == DBEngineEnum.SQLITE
        assert postgres == DBEngineEnum.POSTGRES

    def test_engine_from_value(self):
        """Test comparing engine enum with value."""
        assert DBEngineEnum.SQLITE.value == "django.db.backends.sqlite3"
        assert DBEngineEnum.POSTGRES.value == "django.db.backends.postgresql"

    def test_all_supported_engines(self):
        """Test that all supported engines are present."""
        expected_engines = {"SQLITE", "POSTGRES"}
        actual_engines = {member.name for member in DBEngineEnum}

        assert actual_engines == expected_engines

    def test_engine_iteration(self):
        """Test iterating over database engines."""
        engines = list(DBEngineEnum)

        assert len(engines) == 2
        assert DBEngineEnum.SQLITE in engines
        assert DBEngineEnum.POSTGRES in engines


# ============================================================================
# BASE DATABASE SETTINGS TESTS
# ============================================================================


class TestBaseDatabaseSettings:
    """Test BaseDatabaseSettings configuration."""

    def test_default_base_settings(self, clean_environment):
        """Test base settings with default values."""
        settings = BaseDatabaseSettings()

        assert settings.engine == DBEngineEnum.SQLITE

    def test_base_settings_with_sqlite(self, clean_environment, monkeypatch):
        """Test base settings configured for SQLite."""
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")

        settings = BaseDatabaseSettings()

        assert settings.engine == DBEngineEnum.SQLITE

    def test_base_settings_with_postgres(self, clean_environment, monkeypatch):
        """Test base settings configured for PostgreSQL."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")

        settings = BaseDatabaseSettings()

        assert settings.engine == DBEngineEnum.POSTGRES

    def test_base_settings_engine_from_name(self, clean_environment, monkeypatch):
        """Test setting engine by enum name."""
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")

        settings = BaseDatabaseSettings()

        assert settings.engine == DBEngineEnum.SQLITE

    def test_base_settings_engine_from_value(self, clean_environment, monkeypatch):
        """Test setting engine by enum value."""
        monkeypatch.setenv("DATABASE_ENGINE", "django.db.backends.postgresql")

        settings = BaseDatabaseSettings()

        assert settings.engine == DBEngineEnum.POSTGRES

    def test_base_settings_case_insensitive_engine(self, clean_environment, monkeypatch):
        """Test that engine name is case-insensitive."""
        monkeypatch.setenv("DATABASE_ENGINE", "postgres")  # lowercase

        settings = BaseDatabaseSettings()

        assert settings.engine == DBEngineEnum.POSTGRES

    def test_base_settings_invalid_engine(self, clean_environment, monkeypatch):
        """Test validation error for invalid engine."""
        monkeypatch.setenv("DATABASE_ENGINE", "mysql")  # Not supported

        with pytest.raises(ValidationError) as exc_info:
            BaseDatabaseSettings()

        error_str = str(exc_info.value)
        assert "enum" in error_str.lower()

    def test_base_settings_frozen(self, clean_environment):
        """Test that BaseDatabaseSettings is immutable (frozen)."""
        settings = BaseDatabaseSettings()

        with pytest.raises(ValidationError):
            settings.engine = DBEngineEnum.POSTGRES

    def test_base_settings_extra_fields_ignored(self, clean_environment, monkeypatch):
        """Test that extra environment variables are ignored."""
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")
        monkeypatch.setenv("DATABASE_UNKNOWN_FIELD", "value")

        # Should not raise error
        settings = BaseDatabaseSettings()

        assert settings.engine == DBEngineEnum.SQLITE
        assert not hasattr(settings, "unknown_field")


# ============================================================================
# SQLITE DATABASE SETTINGS TESTS
# ============================================================================


class TestSqliteDatabaseSettings:
    """Test SQLite-specific database settings."""

    def test_sqlite_default_settings(self, clean_environment):
        """Test SQLite settings with defaults."""
        settings = SqliteDatabaseSettings()

        assert settings.engine == DBEngineEnum.SQLITE
        assert "db.sqlite3" in settings.name
        assert settings.name.endswith("db.sqlite3")

    def test_sqlite_custom_name(self, clean_environment, monkeypatch):
        """Test SQLite with custom database name."""
        monkeypatch.setenv("DATABASE_NAME", "custom.db")

        settings = SqliteDatabaseSettings()

        assert settings.name == "custom.db"

    def test_sqlite_name_is_posix_path(self, clean_environment):
        """Test that SQLite name is POSIX-style path."""
        settings = SqliteDatabaseSettings()

        # Should use forward slashes even on Windows
        assert "/" in settings.name or settings.name == "db.sqlite3"
        assert "\\" not in settings.name  # No backslashes

    def test_sqlite_absolute_path(self, clean_environment, monkeypatch):
        """Test SQLite with absolute path."""
        abs_path = "/absolute/path/to/database.sqlite3"
        monkeypatch.setenv("DATABASE_NAME", abs_path)

        settings = SqliteDatabaseSettings()

        assert settings.name == abs_path

    def test_sqlite_relative_path(self, clean_environment, monkeypatch):
        """Test SQLite with relative path."""
        rel_path = "../databases/app.db"
        monkeypatch.setenv("DATABASE_NAME", rel_path)

        settings = SqliteDatabaseSettings()

        assert settings.name == rel_path

    def test_sqlite_memory_database(self, clean_environment, monkeypatch):
        """Test SQLite in-memory database."""
        monkeypatch.setenv("DATABASE_NAME", ":memory:")

        settings = SqliteDatabaseSettings()

        assert settings.name == ":memory:"

    def test_sqlite_no_host_or_port(self, clean_environment):
        """Test that SQLite settings don't have host or port."""
        settings = SqliteDatabaseSettings()

        assert not hasattr(settings, "host")
        assert not hasattr(settings, "port")
        assert not hasattr(settings, "user")
        assert not hasattr(settings, "password")


# ============================================================================
# POSTGRESQL DATABASE SETTINGS TESTS
# ============================================================================


class TestPostgresDatabaseSettings:
    """Test PostgreSQL-specific database settings."""

    def test_postgres_default_settings(self, clean_environment):
        """Test PostgreSQL settings with defaults."""
        settings = PostgresDatabaseSettings()

        assert settings.engine == DBEngineEnum.POSTGRES
        assert settings.name == "gymnassic"
        assert settings.user == "postgres"
        assert settings.password == "postgres"
        assert settings.host == "localhost"
        assert settings.port == 5432

    def test_postgres_custom_all_fields(self, clean_environment, monkeypatch):
        """Test PostgreSQL with all custom fields."""
        monkeypatch.setenv("DATABASE_NAME", "my_app_db")
        monkeypatch.setenv("DATABASE_USER", "app_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "secure_password")
        monkeypatch.setenv("DATABASE_HOST", "db.example.com")
        monkeypatch.setenv("DATABASE_PORT", "5433")

        settings = PostgresDatabaseSettings()

        assert settings.name == "my_app_db"
        assert settings.user == "app_user"
        assert settings.password == "secure_password"
        assert settings.host == "db.example.com"
        assert settings.port == 5433

    def test_postgres_port_as_integer(self, clean_environment, monkeypatch):
        """Test that PostgreSQL port is converted to integer."""
        monkeypatch.setenv("DATABASE_PORT", "5433")

        settings = PostgresDatabaseSettings()

        assert isinstance(settings.port, int)
        assert settings.port == 5433

    def test_postgres_invalid_port_type(self, clean_environment, monkeypatch):
        """Test validation error for non-numeric port."""
        monkeypatch.setenv("DATABASE_PORT", "not_a_number")

        with pytest.raises(ValidationError) as exc_info:
            PostgresDatabaseSettings()

        assert "port" in str(exc_info.value).lower()

    def test_postgres_empty_password_allowed(self, clean_environment, monkeypatch):
        """Test that empty password is allowed (for development)."""
        monkeypatch.setenv("DATABASE_PASSWORD", "")

        settings = PostgresDatabaseSettings()

        # Should use default
        assert settings.password == "postgres"

    def test_postgres_localhost_variants(self, clean_environment, monkeypatch):
        """Test various localhost representations."""
        hosts = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]

        for host in hosts:
            monkeypatch.setenv("DATABASE_HOST", host)
            settings = PostgresDatabaseSettings()
            assert settings.host == host

    def test_postgres_remote_host(self, clean_environment, monkeypatch):
        """Test PostgreSQL with remote host."""
        monkeypatch.setenv("DATABASE_HOST", "prod-db.example.com")

        settings = PostgresDatabaseSettings()

        assert settings.host == "prod-db.example.com"

    def test_postgres_special_chars_in_password(self, clean_environment, monkeypatch):
        """Test PostgreSQL password with special characters."""
        special_password = "P@ss!#$%^&*()_+-=w0rd"
        monkeypatch.setenv("DATABASE_PASSWORD", special_password)

        settings = PostgresDatabaseSettings()

        assert settings.password == special_password

    def test_postgres_database_name_with_underscores(self, clean_environment, monkeypatch):
        """Test PostgreSQL database name with underscores."""
        monkeypatch.setenv("DATABASE_NAME", "my_app_production_db")

        settings = PostgresDatabaseSettings()

        assert settings.name == "my_app_production_db"


# ============================================================================
# DJANGO DATABASES CONTAINER TESTS
# ============================================================================


class TestDjangoDatabases:
    """Test DjangoDatabases container model."""

    def test_django_databases_with_sqlite(self, clean_environment):
        """Test DjangoDatabases with SQLite configuration."""
        sqlite_settings = SqliteDatabaseSettings()
        django_dbs = DjangoDatabases(default=sqlite_settings)

        assert django_dbs.default == sqlite_settings
        assert isinstance(django_dbs.default, SqliteDatabaseSettings)

    def test_django_databases_with_postgres(self, clean_environment):
        """Test DjangoDatabases with PostgreSQL configuration."""
        postgres_settings = PostgresDatabaseSettings()
        django_dbs = DjangoDatabases(default=postgres_settings)

        assert django_dbs.default == postgres_settings
        assert isinstance(django_dbs.default, PostgresDatabaseSettings)

    def test_django_databases_serialization_sqlite(self, clean_environment):
        """Test serializing SQLite DjangoDatabases to dict."""
        sqlite_settings = SqliteDatabaseSettings()
        django_dbs = DjangoDatabases(default=sqlite_settings)

        db_dict = django_dbs.model_dump(mode="json", by_alias=True)

        assert "default" in db_dict
        assert db_dict["default"]["ENGINE"] == "django.db.backends.sqlite3"
        assert "NAME" in db_dict["default"]

    def test_django_databases_serialization_postgres(self, clean_environment, monkeypatch):
        """Test serializing PostgreSQL DjangoDatabases to dict."""
        monkeypatch.setenv("DATABASE_NAME", "test_db")
        monkeypatch.setenv("DATABASE_USER", "test_user")
        
        postgres_settings = PostgresDatabaseSettings()
        django_dbs = DjangoDatabases(default=postgres_settings)

        db_dict = django_dbs.model_dump(mode="json", by_alias=True)

        assert "default" in db_dict
        assert db_dict["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert db_dict["default"]["NAME"] == "test_db"
        assert db_dict["default"]["USER"] == "test_user"
        assert db_dict["default"]["HOST"] == "localhost"
        assert db_dict["default"]["PORT"] == 5432


# ============================================================================
# REAL-WORLD DATABASE SCENARIOS
# ============================================================================


class TestRealWorldDatabaseScenarios:
    """Test real-world database configuration scenarios."""

    def test_local_development_sqlite(self, clean_environment):
        """Test typical local development with SQLite."""
        settings = SqliteDatabaseSettings()

        # Should use local SQLite file
        assert settings.engine == DBEngineEnum.SQLITE
        assert "db.sqlite3" in settings.name
        
        # Convert to Django format
        django_dbs = DjangoDatabases(default=settings)
        db_dict = django_dbs.model_dump(mode="json", by_alias=True)

        assert db_dict["default"]["ENGINE"] == "django.db.backends.sqlite3"

    def test_production_postgresql(self, clean_environment, monkeypatch):
        """Test typical production with PostgreSQL."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "prod_gymnassic")
        monkeypatch.setenv("DATABASE_USER", "prod_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "secure_prod_pass_123")
        monkeypatch.setenv("DATABASE_HOST", "prod-db.example.com")
        monkeypatch.setenv("DATABASE_PORT", "5432")

        settings = PostgresDatabaseSettings()

        assert settings.engine == DBEngineEnum.POSTGRES
        assert settings.name == "prod_gymnassic"
        assert settings.user == "prod_user"
        assert settings.host == "prod-db.example.com"

        # Convert to Django format
        django_dbs = DjangoDatabases(default=settings)
        db_dict = django_dbs.model_dump(mode="json", by_alias=True)

        assert db_dict["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert db_dict["default"]["NAME"] == "prod_gymnassic"

    def test_docker_postgres_connection(self, clean_environment, monkeypatch):
        """Test PostgreSQL connection in Docker environment."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "app_db")
        monkeypatch.setenv("DATABASE_USER", "docker_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "docker_pass")
        monkeypatch.setenv("DATABASE_HOST", "postgres")  # Docker service name
        monkeypatch.setenv("DATABASE_PORT", "5432")

        settings = PostgresDatabaseSettings()

        assert settings.host == "postgres"
        assert settings.name == "app_db"
        assert settings.user == "docker_user"

    def test_staging_environment_config(self, clean_environment, monkeypatch):
        """Test staging environment database configuration."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "staging_gymnassic")
        monkeypatch.setenv("DATABASE_USER", "staging_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "staging_pass")
        monkeypatch.setenv("DATABASE_HOST", "staging-db.internal")
        monkeypatch.setenv("DATABASE_PORT", "5432")

        settings = PostgresDatabaseSettings()

        assert settings.name == "staging_gymnassic"
        assert settings.host == "staging-db.internal"

    def test_ci_cd_test_database(self, clean_environment, monkeypatch):
        """Test CI/CD test database configuration."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "test_gymnassic_ci")
        monkeypatch.setenv("DATABASE_USER", "ci_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "ci_pass")
        monkeypatch.setenv("DATABASE_HOST", "localhost")
        monkeypatch.setenv("DATABASE_PORT", "5432")

        settings = PostgresDatabaseSettings()

        assert settings.name == "test_gymnassic_ci"
        assert settings.user == "ci_user"
        assert settings.host == "localhost"


# ============================================================================
# DATABASE MIGRATION SCENARIOS
# ============================================================================


class TestDatabaseMigrationScenarios:
    """Test database migration and upgrade scenarios."""

    def test_sqlite_to_postgres_migration_prep(self, clean_environment, monkeypatch):
        """Test preparing for SQLite to PostgreSQL migration."""
        # Start with SQLite
        sqlite_settings = SqliteDatabaseSettings()
        assert sqlite_settings.engine == DBEngineEnum.SQLITE

        # Prepare PostgreSQL settings
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "gymnassic")
        monkeypatch.setenv("DATABASE_USER", "app_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "app_pass")

        postgres_settings = PostgresDatabaseSettings()

        # Verify both configurations
        assert sqlite_settings.engine == DBEngineEnum.SQLITE
        assert postgres_settings.engine == DBEngineEnum.POSTGRES
        assert postgres_settings.name == "gymnassic"

    def test_database_connection_pool_settings(self, clean_environment, monkeypatch):
        """Test database connection pool configuration."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "pool_test_db")

        settings = PostgresDatabaseSettings()

        # PostgreSQL supports connection pooling
        assert settings.engine == DBEngineEnum.POSTGRES


# ============================================================================
# ENVIRONMENT-BASED CONFIGURATION TESTS
# ============================================================================


class TestEnvironmentBasedConfiguration:
    """Test configuration based on different environments."""

    def test_local_env_uses_sqlite(self, clean_environment, monkeypatch):
        """Test that local environment typically uses SQLite."""
        os.environ.clear()
        # No DATABASE_ENGINE set, should default to SQLite
        
        base_settings = BaseDatabaseSettings()

        assert base_settings.engine == DBEngineEnum.SQLITE

    def test_production_env_requires_postgres(self, clean_environment, monkeypatch):
        """Test that production environment should use PostgreSQL."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "prod_db")

        base_settings = BaseDatabaseSettings()
        postgres_settings = PostgresDatabaseSettings()

        assert base_settings.engine == DBEngineEnum.POSTGRES
        assert postgres_settings.name == "prod_db"

    def test_env_prefix_used_correctly(self, clean_environment, monkeypatch):
        """Test that DATABASE_ prefix is used for environment variables."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "prefixed_db")

        settings = PostgresDatabaseSettings()

        assert settings.name == "prefixed_db"

    def test_case_sensitive_env_vars(self, clean_environment, monkeypatch):
        """Test that environment variables are case-sensitive."""
        # Set uppercase (correct)
        monkeypatch.setenv("DATABASE_NAME", "correct_name")

        settings = PostgresDatabaseSettings()

        assert settings.name == "correct_name"


# ============================================================================
# EDGE CASES AND VALIDATION TESTS
# ============================================================================


class TestEdgeCasesAndValidation:
    """Test edge cases and boundary conditions."""

    def test_postgres_port_boundary_values(self, clean_environment, monkeypatch):
        """Test PostgreSQL port with boundary values."""
        # Minimum valid port
        monkeypatch.setenv("DATABASE_PORT", "1")
        settings = PostgresDatabaseSettings()
        assert settings.port == 1

        # Maximum valid port
        monkeypatch.setenv("DATABASE_PORT", "65535")
        settings = PostgresDatabaseSettings()
        assert settings.port == 65535

        # Common PostgreSQL port
        monkeypatch.setenv("DATABASE_PORT", "5432")
        settings = PostgresDatabaseSettings()
        assert settings.port == 5432

    def test_very_long_database_name(self, clean_environment, monkeypatch):
        """Test handling of very long database name."""
        long_name = "a" * 255  # Typical max length
        monkeypatch.setenv("DATABASE_NAME", long_name)

        settings = PostgresDatabaseSettings()

        assert settings.name == long_name
        assert len(settings.name) == 255

    def test_unicode_in_database_credentials(self, clean_environment, monkeypatch):
        """Test Unicode characters in database credentials."""
        monkeypatch.setenv("DATABASE_USER", "user_ñ_ü")
        monkeypatch.setenv("DATABASE_PASSWORD", "pāss_wôrd_123")

        settings = PostgresDatabaseSettings()

        assert settings.user == "user_ñ_ü"
        assert settings.password == "pāss_wôrd_123"

    def test_empty_database_name_uses_default(self, clean_environment, monkeypatch):
        """Test that empty database name uses default."""
        monkeypatch.setenv("DATABASE_NAME", "")

        settings = PostgresDatabaseSettings()

        # Should use default value
        assert settings.name == "gymnassic"

    def test_whitespace_in_credentials(self, clean_environment, monkeypatch):
        """Test handling of whitespace in credentials."""
        monkeypatch.setenv("DATABASE_PASSWORD", "   password with spaces   ")

        settings = PostgresDatabaseSettings()

        # Pydantic does not strip by default
        assert settings.password == "   password with spaces   "
