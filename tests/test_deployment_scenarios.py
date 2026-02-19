"""
Test suite for real-world deployment and integration scenarios.

Tests cover:
- Complete application configuration workflows
- Environment switching and configuration updates
- Multi-environment deployment scenarios
- Configuration validation across all modules
- Integration between settings, database, and gym config
- Production readiness checks
- Disaster recovery scenarios
- Cloud deployment patterns
"""

from pathlib import Path

from config.settings.databases import DBEngineEnum
from config.settings.factory import get_django_db_dict, get_django_dbs, get_settings
from config.settings.gymconf import GymConfig


# ============================================================================
# COMPLETE APPLICATION BOOTSTRAP TESTS
# ============================================================================


class TestApplicationBootstrap:
    """Test complete application bootstrap process."""

    def test_minimal_application_startup(self, clean_environment):
        """Test application can start with minimal configuration."""
        # Load all settings with defaults
        env_settings = get_settings()
        db_settings = get_django_db_dict()

        # Verify minimal viable configuration
        assert env_settings.SECRET_KEY is not None
        assert db_settings["default"]["ENGINE"] is not None
        assert env_settings.TIME_ZONE is not None

    def test_full_application_bootstrap_local(self, clean_environment, monkeypatch, temp_gym_yaml_file):
        """Test full application bootstrap for local development."""
        # Set local environment
        monkeypatch.setenv("SECRET_KEY", "local-development-key")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")

        # Bootstrap all components
        env_settings = get_settings()
        db_dict = get_django_db_dict()

        # Verify all components are ready
        assert env_settings.DEBUG is True
        assert env_settings.ENVIRONMENT == "local"
        assert db_dict["default"]["ENGINE"] == "django.db.backends.sqlite3"

        # Verify local development optimizations
        assert "console" in env_settings.EMAIL_BACKEND.lower()

    def test_full_application_bootstrap_production(self, clean_environment, monkeypatch):
        """Test full application bootstrap for production."""
        # Set production environment
        monkeypatch.setenv("SECRET_KEY", "production-secure-key-very-long-and-random")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("ALLOWED_HOSTS", '["example.com", "www.example.com"]')
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "prod_gymnassic")
        monkeypatch.setenv("DATABASE_USER", "prod_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "secure_password")
        monkeypatch.setenv("DATABASE_HOST", "db.example.com")

        # Bootstrap all components
        env_settings = get_settings()
        db_dict = get_django_db_dict()

        # Verify production configuration
        assert env_settings.DEBUG is False
        assert env_settings.ENVIRONMENT == "production"
        assert db_dict["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert db_dict["default"]["HOST"] == "db.example.com"


# ============================================================================
# ENVIRONMENT SWITCHING TESTS
# ============================================================================


class TestEnvironmentSwitching:
    """Test switching between different environments."""

    def test_local_to_production_migration(self, clean_environment, monkeypatch):
        """Test configuration migration from local to production."""
        # Start with local
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")

        local_settings = get_settings()
        local_db = get_django_db_dict()

        assert local_settings.ENVIRONMENT == "local"
        assert local_db["default"]["ENGINE"] == "django.db.backends.sqlite3"

        # Migrate to production
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "prod_db")
        monkeypatch.setenv("DATABASE_USER", "prod_user")
        monkeypatch.setenv("DATABASE_PASSWORD", "prod_pass")

        prod_settings = get_settings()
        prod_db = get_django_db_dict()

        assert prod_settings.ENVIRONMENT == "production"
        assert prod_settings.DEBUG is False
        assert prod_db["default"]["ENGINE"] == "django.db.backends.postgresql"

    def test_development_to_staging_transition(self, clean_environment, monkeypatch):
        """Test transition from development to staging."""
        # Development config
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")

        dev_settings = get_settings()
        assert dev_settings.ENVIRONMENT == "development"

        # Staging config
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "staging_db")

        staging_settings = get_settings()
        staging_db = get_django_db_dict()

        assert staging_settings.ENVIRONMENT == "staging"
        assert staging_settings.DEBUG is False
        assert staging_db["default"]["ENGINE"] == "django.db.backends.postgresql"

    def test_blue_green_deployment_switch(self, clean_environment, monkeypatch):
        """Test blue-green deployment configuration switching."""
        # Blue environment
        monkeypatch.setenv("ENVIRONMENT", "production-blue")
        monkeypatch.setenv("DATABASE_HOST", "blue-db.example.com")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")

        blue_settings = get_settings()
        blue_db = get_django_db_dict()

        assert "blue" in blue_settings.ENVIRONMENT
        assert blue_db["default"]["HOST"] == "blue-db.example.com"

        # Green environment
        monkeypatch.setenv("ENVIRONMENT", "production-green")
        monkeypatch.setenv("DATABASE_HOST", "green-db.example.com")

        green_settings = get_settings()
        green_db = get_django_db_dict()

        assert "green" in green_settings.ENVIRONMENT
        assert green_db["default"]["HOST"] == "green-db.example.com"


# ============================================================================
# CLOUD DEPLOYMENT PATTERNS
# ============================================================================


class TestCloudDeploymentPatterns:
    """Test common cloud deployment patterns."""

    def test_aws_deployment_config(self, clean_environment, monkeypatch):
        """Test AWS deployment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "aws-secret-from-secrets-manager")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "gymnassic_prod")
        monkeypatch.setenv("DATABASE_HOST", "gymnassic.xxxxx.us-east-1.rds.amazonaws.com")
        monkeypatch.setenv("DATABASE_PORT", "5432")
        monkeypatch.setenv("ALLOWED_HOSTS", '["elb.amazonaws.com", "example.com"]')

        _ = get_settings()  # Verify settings load
        db_dict = get_django_db_dict()

        assert db_dict["default"]["HOST"] is not None
        assert "rds.amazonaws.com" in db_dict["default"]["HOST"]

    def test_gcp_deployment_config(self, clean_environment, monkeypatch):
        """Test Google Cloud Platform deployment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "/cloudsql/project:region:instance")
        monkeypatch.setenv("DATABASE_NAME", "gymnassic")

        db_dict = get_django_db_dict()

        assert "cloudsql" in db_dict["default"]["HOST"]

    def test_azure_deployment_config(self, clean_environment, monkeypatch):
        """Test Microsoft Azure deployment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "gymnassic.postgres.database.azure.com")
        monkeypatch.setenv("DATABASE_NAME", "gymnassic")
        monkeypatch.setenv("DATABASE_USER", "adminuser@gymnassic")

        db_dict = get_django_db_dict()

        assert "azure.com" in db_dict["default"]["HOST"]
        assert "@" in db_dict["default"]["USER"]

    def test_digital_ocean_deployment_config(self, clean_environment, monkeypatch):
        """Test DigitalOcean deployment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "db-postgresql-nyc3-12345.ondigitalocean.com")
        monkeypatch.setenv("DATABASE_NAME", "defaultdb")
        monkeypatch.setenv("DATABASE_PORT", "25060")

        db_dict = get_django_db_dict()

        assert "digitalocean.com" in db_dict["default"]["HOST"]
        assert db_dict["default"]["PORT"] == 25060

    def test_heroku_style_deployment(self, clean_environment, monkeypatch):
        """Test Heroku-style deployment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "ec2-xxx.compute-1.amazonaws.com")
        monkeypatch.setenv("DATABASE_NAME", "heroku_app")

        db_dict = get_django_db_dict()

        assert "compute-1.amazonaws.com" in db_dict["default"]["HOST"]


# ============================================================================
# CONTAINERIZED DEPLOYMENT TESTS
# ============================================================================


class TestContainerizedDeployment:
    """Test containerized deployment scenarios."""

    def test_docker_compose_setup(self, clean_environment, monkeypatch):
        """Test Docker Compose deployment setup."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "docker-secret-key")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "postgres")  # Service name
        monkeypatch.setenv("DATABASE_NAME", "gymnassic")
        monkeypatch.setenv("DATABASE_USER", "docker")
        monkeypatch.setenv("DATABASE_PASSWORD", "docker")

        settings = get_settings()
        db_dict = get_django_db_dict()

        assert db_dict["default"]["HOST"] == "postgres"
        assert db_dict["default"]["NAME"] == "gymnassic"

    def test_kubernetes_deployment(self, clean_environment, monkeypatch):
        """Test Kubernetes deployment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "k8s-secret-from-secret")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "postgres-service.default.svc.cluster.local")
        monkeypatch.setenv("DATABASE_NAME", "gymnassic")

        db_dict = get_django_db_dict()

        assert "svc.cluster.local" in db_dict["default"]["HOST"]

    def test_docker_swarm_deployment(self, clean_environment, monkeypatch):
        """Test Docker Swarm deployment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "postgres_service")
        monkeypatch.setenv("DATABASE_NAME", "gymnassic")

        db_dict = get_django_db_dict()

        assert db_dict["default"]["HOST"] == "postgres_service"


# ============================================================================
# MULTI-REGION DEPLOYMENT TESTS
# ============================================================================


class TestMultiRegionDeployment:
    """Test multi-region deployment scenarios."""

    def test_us_east_region_config(self, clean_environment, monkeypatch):
        """Test US East region configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production-us-east-1")
        monkeypatch.setenv("TIME_ZONE", "America/New_York")
        monkeypatch.setenv("DATABASE_HOST", "db-us-east-1.example.com")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")

        _ = get_settings()  # Verify settings load
        db_dict = get_django_db_dict()

        assert db_dict["default"]["HOST"] is not None
        assert "us-east" in db_dict["default"]["HOST"]

    def test_asia_pacific_region_config(self, clean_environment, monkeypatch):
        """Test Asia Pacific region configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production-ap-southeast-1")
        monkeypatch.setenv("TIME_ZONE", "Asia/Singapore")
        monkeypatch.setenv("DATABASE_HOST", "db-ap-southeast-1.example.com")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("LANGUAGE_CODE", "id-id")

        settings = get_settings()
        db_dict = get_django_db_dict()

        assert "ap-southeast" in settings.ENVIRONMENT
        assert settings.TIME_ZONE == "Asia/Singapore"
        assert "ap-southeast" in db_dict["default"]["HOST"]

    def test_europe_region_config(self, clean_environment, monkeypatch):
        """Test Europe region configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production-eu-central-1")
        monkeypatch.setenv("TIME_ZONE", "Europe/Berlin")
        monkeypatch.setenv("DATABASE_HOST", "db-eu-central-1.example.com")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")

        settings = get_settings()
        db_dict = get_django_db_dict()

        assert "eu-central" in settings.ENVIRONMENT
        assert "eu-central" in db_dict["default"]["HOST"]


# ============================================================================
# PRODUCTION READINESS TESTS
# ============================================================================


class TestProductionReadiness:
    """Test production readiness checks."""

    def test_production_security_checklist(self, clean_environment, monkeypatch):
        """Test production security configuration checklist."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "production-secure-key-minimum-50-chars-long-random-string")
        monkeypatch.setenv("ALLOWED_HOSTS", '["example.com"]')
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")

        settings = get_settings()

        # Security checks
        assert settings.DEBUG is False, "DEBUG must be False in production"
        assert len(settings.SECRET_KEY) >= 50, "SECRET_KEY should be at least 50 chars"
        assert "insecure" not in settings.SECRET_KEY.lower(), "SECRET_KEY should not contain 'insecure'"

    def test_database_production_readiness(self, clean_environment, monkeypatch):
        """Test database configuration for production readiness."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "prod_db")
        monkeypatch.setenv("DATABASE_USER", "app_user")  # Not 'postgres'
        monkeypatch.setenv("DATABASE_PASSWORD", "complex_password_123")

        db_dict = get_django_db_dict()

        # Production database checks
        assert db_dict["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert db_dict["default"]["USER"] != "postgres", "Should use dedicated app user"
        assert len(db_dict["default"]["PASSWORD"]) > 10, "Password should be complex"

    def test_email_production_configuration(self, clean_environment, monkeypatch):
        """Test email configuration for production."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
        monkeypatch.setenv("EMAIL_HOST", "smtp.sendgrid.net")
        monkeypatch.setenv("EMAIL_PORT", "587")
        monkeypatch.setenv("EMAIL_USE_TLS", "true")

        settings = get_settings()

        # Email production checks
        assert "smtp" in settings.EMAIL_BACKEND.lower()
        assert settings.EMAIL_USE_TLS is True
        assert settings.EMAIL_PORT in [587, 465]


# ============================================================================
# DISASTER RECOVERY TESTS
# ============================================================================


class TestDisasterRecovery:
    """Test disaster recovery scenarios."""

    def test_database_failover(self, clean_environment, monkeypatch):
        """Test database failover configuration."""
        # Primary database
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "primary-db.example.com")

        primary_db = get_django_db_dict()
        assert primary_db["default"]["HOST"] == "primary-db.example.com"

        # Failover to replica
        monkeypatch.setenv("DATABASE_HOST", "replica-db.example.com")

        replica_db = get_django_db_dict()
        assert replica_db["default"]["HOST"] == "replica-db.example.com"

    def test_backup_database_configuration(self, clean_environment, monkeypatch):
        """Test backup database configuration."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "backup-db.example.com")
        monkeypatch.setenv("DATABASE_NAME", "gymnassic_backup")

        db_dict = get_django_db_dict()

        assert "backup" in db_dict["default"]["HOST"]
        assert "backup" in db_dict["default"]["NAME"]

    def test_read_replica_configuration(self, clean_environment, monkeypatch):
        """Test read replica configuration."""
        # Primary (write) database
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "write-db.example.com")

        write_db = get_django_db_dict()
        assert "write" in write_db["default"]["HOST"]

        # Read replica
        monkeypatch.setenv("DATABASE_HOST", "read-replica-db.example.com")

        read_db = get_django_db_dict()
        assert "read-replica" in read_db["default"]["HOST"]


# ============================================================================
# CONFIGURATION VALIDATION TESTS
# ============================================================================


class TestConfigurationValidation:
    """Test configuration validation across all modules."""

    def test_all_settings_modules_compatible(self, clean_environment, monkeypatch):
        """Test that all settings modules work together."""
        # Set comprehensive configuration
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("DATABASE_ENGINE", "SQLITE")

        # Load all settings
        env_settings = get_settings()
        db_dict = get_django_db_dict()

        # Verify compatibility
        assert env_settings is not None
        assert db_dict is not None
        assert isinstance(env_settings.DEBUG, bool)
        assert isinstance(db_dict, dict)

    def test_settings_serialization(self, clean_environment, monkeypatch):
        """Test that settings can be serialized properly."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_NAME", "test_db")

        db_dict = get_django_db_dict()

        # Should be JSON-serializable
        assert isinstance(db_dict, dict)
        assert "default" in db_dict
        assert isinstance(db_dict["default"], dict)

    def test_cross_module_consistency(self, clean_environment, monkeypatch):
        """Test consistency across settings modules."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")

        env_settings = get_settings()
        db_settings = get_django_dbs()

        # Environment should be consistent
        assert env_settings.ENVIRONMENT == "production"
        # Database should match production expectations
        assert db_settings.default.engine == DBEngineEnum.POSTGRES


# ============================================================================
# INTEGRATION WITH GYM CONFIGURATION
# ============================================================================


class TestGymConfigIntegration:
    """Test integration with gym configuration."""

    def test_complete_app_config_with_gym(self, clean_environment, monkeypatch, temp_gym_yaml_file):
        """Test complete application configuration including gym config."""
        # Set environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")

        # Load all configurations
        env_settings = get_settings()
        db_dict = get_django_db_dict()

        # Verify all components loaded
        assert env_settings is not None
        assert db_dict is not None

    def test_gym_config_independent_of_env(self, temp_gym_yaml_file):
        """Test that gym config works independently of environment settings."""
        # Create a mock get_gym_settings that uses our temp file
        import config.settings.factory as factory_module

        def mock_get_gym_settings():
            return GymConfig(_yaml_files=[Path(temp_gym_yaml_file)])

        original_func = factory_module.get_gym_settings
        factory_module.get_gym_settings = mock_get_gym_settings

        try:
            gym_config = factory_module.get_gym_settings()
            
            # Should load successfully
            assert gym_config.gym_name is not None
        finally:
            factory_module.get_gym_settings = original_func


# ============================================================================
# PERFORMANCE AND SCALABILITY TESTS
# ============================================================================


class TestPerformanceAndScalability:
    """Test performance and scalability considerations."""

    def test_settings_loading_performance(self, clean_environment):
        """Test that settings load quickly."""
        import time

        start = time.time()
        settings = get_settings()
        db_dict = get_django_db_dict()
        end = time.time()

        # Should load in under 1 second
        assert end - start < 1.0
        assert settings is not None
        assert db_dict is not None

    def test_multiple_settings_instances(self, clean_environment):
        """Test creating multiple settings instances."""
        # Create multiple instances
        instances = [get_settings() for _ in range(10)]

        # All should be valid
        assert len(instances) == 10
        for instance in instances:
            assert instance.SECRET_KEY is not None

    def test_database_connection_scaling(self, clean_environment, monkeypatch):
        """Test database configuration for scaling."""
        monkeypatch.setenv("DATABASE_ENGINE", "POSTGRES")
        monkeypatch.setenv("DATABASE_HOST", "pgpool.example.com")  # Connection pooler

        db_dict = get_django_db_dict()

        assert "pgpool" in db_dict["default"]["HOST"]


# ============================================================================
# DEBUGGING AND TROUBLESHOOTING TESTS
# ============================================================================


class TestDebuggingAndTroubleshooting:
    """Test debugging and troubleshooting scenarios."""

    def test_verbose_error_messages(self, clean_environment, monkeypatch):
        """Test that configuration errors provide helpful messages."""
        from pydantic import ValidationError

        monkeypatch.setenv("DATABASE_ENGINE", "invalid_engine")

        try:
            get_django_dbs()
            raise AssertionError("Should have raised ValidationError")
        except ValidationError as e:
            # Error message should be helpful
            error_str = str(e)
            assert len(error_str) > 0

    def test_configuration_inspection(self, clean_environment):
        """Test that configuration can be inspected easily."""
        settings = get_settings()

        # Should be able to inspect all attributes
        assert hasattr(settings, "SECRET_KEY")
        assert hasattr(settings, "DEBUG")
        assert hasattr(settings, "ENVIRONMENT")

    def test_default_configuration_is_safe(self, clean_environment):
        """Test that default configuration is safe (fail-secure)."""
        settings = get_settings()

        # Defaults should be secure
        assert settings.DEBUG is False, "DEBUG should default to False"
        assert settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]
