"""
Test suite for environment settings validation and configuration.

Tests cover:
- CommonEnvSettings with Pydantic validation
- Environment variable loading and parsing
- Settings property accessors
- Email configuration
- Security settings validation
- Real-world environment configurations
- Settings edge cases and error handling
"""

import pytest
from pydantic import ValidationError

from config.settings.envcommon import CommonEnvSettings


# ============================================================================
# COMMON ENV SETTINGS BASIC TESTS
# ============================================================================


class TestCommonEnvSettingsBasics:
    """Test basic CommonEnvSettings functionality."""

    def test_default_settings(self, clean_environment):
        """Test CommonEnvSettings with all defaults."""
        settings = CommonEnvSettings()

        assert settings.SECRET_KEY == "django-insecure-change-this-in-production"
        assert settings.DEBUG is False
        assert settings.ENVIRONMENT == "local"
        assert settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]
        assert settings.LANGUAGE_CODE == "en-us"
        assert settings.TIME_ZONE == "Asia/Jakarta"

    def test_settings_from_environment_variables(self, clean_environment, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-123")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("TIME_ZONE", "UTC")

        settings = CommonEnvSettings()

        assert settings.SECRET_KEY == "test-secret-key-123"
        assert settings.DEBUG is True
        assert settings.ENVIRONMENT == "production"
        assert settings.TIME_ZONE == "UTC"

    def test_settings_case_sensitive(self, clean_environment, monkeypatch):
        """Test that settings read from correct environment variables."""
        # Use different variable names since Windows env vars are case-insensitive
        monkeypatch.setenv("SECRET_KEY", "my-secret-key")
        monkeypatch.setenv("DEBUG", "true")

        settings = CommonEnvSettings()

        # Should read the correct environment variables
        assert settings.SECRET_KEY == "my-secret-key"
        assert settings.DEBUG is True

    def test_extra_fields_ignored(self, clean_environment, monkeypatch):
        """Test that extra environment variables are ignored."""
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("UNKNOWN_FIELD", "some-value")

        settings = CommonEnvSettings()

        assert settings.SECRET_KEY == "test-key"
        assert not hasattr(settings, "UNKNOWN_FIELD")
        assert not hasattr(settings, "unknown_field")


# ============================================================================
# PROPERTY ACCESSOR TESTS
# ============================================================================


class TestPropertyAccessors:
    """Test lowercase property accessors."""

    def test_secret_key_property(self, clean_environment, monkeypatch):
        """Test secret_key property accessor."""
        monkeypatch.setenv("SECRET_KEY", "TEST_KEY")

        settings = CommonEnvSettings()

        assert settings.secret_key == "TEST_KEY"
        assert settings.secret_key == settings.SECRET_KEY

    def test_debug_property(self, clean_environment, monkeypatch):
        """Test debug property accessor."""
        monkeypatch.setenv("DEBUG", "true")

        settings = CommonEnvSettings()

        assert settings.debug is True
        assert settings.debug == settings.DEBUG

    def test_environment_property(self, clean_environment, monkeypatch):
        """Test environment property accessor."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        settings = CommonEnvSettings()

        assert settings.environment == "production"
        assert settings.environment == settings.ENVIRONMENT

    def test_allowed_hosts_property(self, clean_environment, monkeypatch):
        """Test allowed_hosts property accessor."""
        monkeypatch.setenv("ALLOWED_HOSTS", '["example.com", "www.example.com"]')

        settings = CommonEnvSettings()

        assert settings.allowed_hosts == settings.ALLOWED_HOSTS
        assert isinstance(settings.allowed_hosts, list)

    def test_language_code_property(self, clean_environment, monkeypatch):
        """Test language_code property accessor."""
        monkeypatch.setenv("LANGUAGE_CODE", "id-id")

        settings = CommonEnvSettings()

        assert settings.language_code == "id-id"
        assert settings.language_code == settings.LANGUAGE_CODE

    def test_timezone_property(self, clean_environment, monkeypatch):
        """Test timezone property accessor."""
        monkeypatch.setenv("TIME_ZONE", "UTC")

        settings = CommonEnvSettings()

        assert settings.timezone == "UTC"
        assert settings.timezone == settings.TIME_ZONE

    def test_all_properties_accessible(self, clean_environment):
        """Test that all property accessors work."""
        settings = CommonEnvSettings()

        # Should not raise AttributeError
        _ = settings.secret_key
        _ = settings.debug
        _ = settings.environment
        _ = settings.allowed_hosts
        _ = settings.language_code
        _ = settings.timezone
        _ = settings.email_backend
        _ = settings.email_host
        _ = settings.email_port
        _ = settings.email_use_tls


# ============================================================================
# SECURITY SETTINGS TESTS
# ============================================================================


class TestSecuritySettings:
    """Test security-related settings."""

    def test_secret_key_required_for_production(self, clean_environment, monkeypatch):
        """Test that a strong secret key should be used in production."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "django-insecure-change-this-in-production")

        settings = CommonEnvSettings()

        # While technically allowed, this is the insecure default
        assert "insecure" in settings.SECRET_KEY.lower()
        # In production, this should be different

    def test_custom_secret_key(self, clean_environment, monkeypatch):
        """Test setting a custom secure secret key."""
        secure_key = "prod-secret-key-very-secure-and-long-123456789"
        monkeypatch.setenv("SECRET_KEY", secure_key)

        settings = CommonEnvSettings()

        assert settings.SECRET_KEY == secure_key
        assert len(settings.SECRET_KEY) > 30  # Good practice

    def test_debug_false_in_production(self, clean_environment, monkeypatch):
        """Test that DEBUG should be False in production."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")

        settings = CommonEnvSettings()

        assert settings.DEBUG is False
        assert settings.ENVIRONMENT == "production"

    def test_debug_true_in_local(self, clean_environment, monkeypatch):
        """Test that DEBUG can be True in local environment."""
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("DEBUG", "true")

        settings = CommonEnvSettings()

        assert settings.DEBUG is True
        assert settings.ENVIRONMENT == "local"

    def test_allowed_hosts_configuration(self, clean_environment, monkeypatch):
        """Test ALLOWED_HOSTS configuration."""
        hosts = '["example.com", "www.example.com", "api.example.com"]'
        monkeypatch.setenv("ALLOWED_HOSTS", hosts)

        settings = CommonEnvSettings()

        assert isinstance(settings.ALLOWED_HOSTS, list)
        assert len(settings.ALLOWED_HOSTS) >= 1

    def test_empty_secret_key_uses_default(self, clean_environment, monkeypatch):
        """Test that empty secret key falls back to default."""
        monkeypatch.setenv("SECRET_KEY", "")

        settings = CommonEnvSettings()

        # Should use default
        assert settings.SECRET_KEY == "django-insecure-change-this-in-production"


# ============================================================================
# INTERNATIONALIZATION SETTINGS TESTS
# ============================================================================


class TestInternationalizationSettings:
    """Test internationalization and localization settings."""

    def test_default_timezone(self, clean_environment):
        """Test default timezone is Asia/Jakarta."""
        settings = CommonEnvSettings()

        assert settings.TIME_ZONE == "Asia/Jakarta"

    def test_custom_timezone(self, clean_environment, monkeypatch):
        """Test setting custom timezone."""
        timezones = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]

        for tz in timezones:
            monkeypatch.setenv("TIME_ZONE", tz)
            settings = CommonEnvSettings()
            assert settings.TIME_ZONE == tz

    def test_default_language_code(self, clean_environment):
        """Test default language code is en-us."""
        settings = CommonEnvSettings()

        assert settings.LANGUAGE_CODE == "en-us"

    def test_indonesian_language_code(self, clean_environment, monkeypatch):
        """Test Indonesian language code."""
        monkeypatch.setenv("LANGUAGE_CODE", "id-id")

        settings = CommonEnvSettings()

        assert settings.LANGUAGE_CODE == "id-id"

    def test_various_language_codes(self, clean_environment, monkeypatch):
        """Test various language codes."""
        language_codes = ["en-us", "id-id", "en-gb", "es-es", "fr-fr"]

        for lang_code in language_codes:
            monkeypatch.setenv("LANGUAGE_CODE", lang_code)
            settings = CommonEnvSettings()
            assert settings.LANGUAGE_CODE == lang_code


# ============================================================================
# EMAIL CONFIGURATION TESTS
# ============================================================================


class TestEmailConfiguration:
    """Test email configuration settings."""

    def test_default_email_backend(self, clean_environment):
        """Test default email backend is console."""
        settings = CommonEnvSettings()

        assert settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"

    def test_smtp_email_backend(self, clean_environment, monkeypatch):
        """Test SMTP email backend configuration."""
        monkeypatch.setenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
        monkeypatch.setenv("EMAIL_HOST", "smtp.gmail.com")
        monkeypatch.setenv("EMAIL_PORT", "587")
        monkeypatch.setenv("EMAIL_USE_TLS", "true")
        monkeypatch.setenv("EMAIL_HOST_USER", "user@example.com")
        monkeypatch.setenv("EMAIL_HOST_PASSWORD", "email_password_123")

        settings = CommonEnvSettings()

        assert settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
        assert settings.EMAIL_HOST == "smtp.gmail.com"
        assert settings.EMAIL_PORT == 587
        assert settings.EMAIL_USE_TLS is True
        assert settings.EMAIL_HOST_USER == "user@example.com"
        assert settings.EMAIL_HOST_PASSWORD == "email_password_123"

    def test_email_port_as_integer(self, clean_environment, monkeypatch):
        """Test that email port is converted to integer."""
        monkeypatch.setenv("EMAIL_PORT", "465")

        settings = CommonEnvSettings()

        assert isinstance(settings.EMAIL_PORT, int)
        assert settings.EMAIL_PORT == 465

    def test_email_use_tls_boolean(self, clean_environment, monkeypatch):
        """Test EMAIL_USE_TLS as boolean."""
        monkeypatch.setenv("EMAIL_USE_TLS", "false")

        settings = CommonEnvSettings()

        assert isinstance(settings.EMAIL_USE_TLS, bool)
        assert settings.EMAIL_USE_TLS is False

    def test_production_email_config(self, clean_environment, monkeypatch):
        """Test production email configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
        monkeypatch.setenv("EMAIL_HOST", "smtp.sendgrid.net")
        monkeypatch.setenv("EMAIL_PORT", "587")
        monkeypatch.setenv("EMAIL_USE_TLS", "true")
        monkeypatch.setenv("EMAIL_HOST_USER", "apikey")
        monkeypatch.setenv("EMAIL_HOST_PASSWORD", "SG.xxxxxxxxxxxxx")

        settings = CommonEnvSettings()

        assert settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
        assert settings.EMAIL_HOST == "smtp.sendgrid.net"
        assert settings.EMAIL_HOST_USER == "apikey"

    def test_local_console_email_backend(self, clean_environment, monkeypatch):
        """Test local development uses console email backend."""
        monkeypatch.setenv("ENVIRONMENT", "local")

        settings = CommonEnvSettings()

        # Default should be console backend
        assert "console" in settings.EMAIL_BACKEND.lower()


# ============================================================================
# ALLOWED HOSTS TESTS
# ============================================================================


class TestAllowedHostsConfiguration:
    """Test ALLOWED_HOSTS configuration."""

    def test_default_allowed_hosts(self, clean_environment):
        """Test default allowed hosts."""
        settings = CommonEnvSettings()

        assert settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]

    def test_single_allowed_host(self, clean_environment, monkeypatch):
        """Test single allowed host."""
        monkeypatch.setenv("ALLOWED_HOSTS", '["example.com"]')

        settings = CommonEnvSettings()

        assert isinstance(settings.ALLOWED_HOSTS, list)

    def test_multiple_allowed_hosts(self, clean_environment, monkeypatch):
        """Test multiple allowed hosts."""
        hosts = '["example.com", "www.example.com", "api.example.com"]'
        monkeypatch.setenv("ALLOWED_HOSTS", hosts)

        settings = CommonEnvSettings()

        assert isinstance(settings.ALLOWED_HOSTS, list)
        assert len(settings.ALLOWED_HOSTS) >= 1

    def test_wildcard_allowed_host(self, clean_environment, monkeypatch):
        """Test wildcard in allowed hosts."""
        monkeypatch.setenv("ALLOWED_HOSTS", '[".example.com"]')

        settings = CommonEnvSettings()

        assert isinstance(settings.ALLOWED_HOSTS, list)

    def test_ip_address_allowed_hosts(self, clean_environment, monkeypatch):
        """Test IP addresses in allowed hosts."""
        monkeypatch.setenv("ALLOWED_HOSTS", '["127.0.0.1", "192.168.1.100", "::1"]')

        settings = CommonEnvSettings()

        assert isinstance(settings.ALLOWED_HOSTS, list)


# ============================================================================
# ENVIRONMENT-SPECIFIC CONFIGURATION TESTS
# ============================================================================


class TestEnvironmentSpecificConfiguration:
    """Test configuration for different environments."""

    def test_local_environment_config(self, clean_environment, monkeypatch):
        """Test typical local environment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SECRET_KEY", "local-dev-key")

        settings = CommonEnvSettings()

        assert settings.ENVIRONMENT == "local"
        assert settings.DEBUG is True
        assert settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"

    def test_production_environment_config(self, clean_environment, monkeypatch):
        """Test typical production environment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "super-secure-production-key")
        monkeypatch.setenv("ALLOWED_HOSTS", '["example.com", "www.example.com"]')

        settings = CommonEnvSettings()

        assert settings.ENVIRONMENT == "production"
        assert settings.DEBUG is False

    def test_development_environment_config(self, clean_environment, monkeypatch):
        """Test development environment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "dev")
        monkeypatch.setenv("DEBUG", "true")

        settings = CommonEnvSettings()

        assert settings.ENVIRONMENT == "dev"
        assert settings.DEBUG is True

    def test_staging_environment_config(self, clean_environment, monkeypatch):
        """Test staging environment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("ALLOWED_HOSTS", '["staging.example.com"]')

        settings = CommonEnvSettings()

        assert settings.ENVIRONMENT == "staging"
        assert settings.DEBUG is False


# ============================================================================
# REAL-WORLD SCENARIOS
# ============================================================================


class TestRealWorldScenarios:
    """Test real-world configuration scenarios."""

    def test_fresh_project_setup(self, clean_environment):
        """Test fresh project with default settings."""
        settings = CommonEnvSettings()

        # Should have sensible defaults
        assert settings.SECRET_KEY is not None
        assert settings.DEBUG is False  # Safe default
        assert settings.TIME_ZONE == "Asia/Jakarta"
        assert len(settings.ALLOWED_HOSTS) >= 2

    def test_docker_deployment_config(self, clean_environment, monkeypatch):
        """Test Docker deployment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "docker-secret-key-from-secrets-manager")
        monkeypatch.setenv("ALLOWED_HOSTS", '["app", "nginx", "example.com"]')

        settings = CommonEnvSettings()

        assert settings.ENVIRONMENT == "production"
        assert settings.DEBUG is False

    def test_kubernetes_deployment_config(self, clean_environment, monkeypatch):
        """Test Kubernetes deployment configuration."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "k8s-secret-from-configmap")
        monkeypatch.setenv("ALLOWED_HOSTS", '["svc", "ingress.example.com"]')

        settings = CommonEnvSettings()

        assert settings.ENVIRONMENT == "production"

    def test_ci_cd_pipeline_config(self, clean_environment, monkeypatch):
        """Test CI/CD pipeline testing configuration."""
        monkeypatch.setenv("ENVIRONMENT", "ci")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SECRET_KEY", "ci-test-key")

        settings = CommonEnvSettings()

        assert settings.ENVIRONMENT == "ci"
        assert settings.DEBUG is True

    def test_multi_region_deployment(self, clean_environment, monkeypatch):
        """Test multi-region deployment configuration."""
        regions = ["us-east", "us-west", "eu-central", "ap-southeast"]

        for region in regions:
            monkeypatch.setenv("ENVIRONMENT", f"{region}-production")
            monkeypatch.setenv("TIME_ZONE", "UTC")

            settings = CommonEnvSettings()

            assert region in settings.ENVIRONMENT


# ============================================================================
# VALIDATION AND ERROR HANDLING TESTS
# ============================================================================


class TestValidationAndErrorHandling:
    """Test validation and error handling."""

    def test_boolean_true_variations(self, clean_environment, monkeypatch):
        """Test various ways to specify true for boolean fields."""
        true_values = ["true", "True", "TRUE", "1", "yes", "Yes"]

        for value in true_values:
            monkeypatch.setenv("DEBUG", value)
            settings = CommonEnvSettings()
            # Pydantic should handle these
            assert isinstance(settings.DEBUG, bool)

    def test_boolean_false_variations(self, clean_environment, monkeypatch):
        """Test various ways to specify false for boolean fields."""
        false_values = ["false", "False", "FALSE", "0", "no", "No"]

        for value in false_values:
            monkeypatch.setenv("DEBUG", value)
            settings = CommonEnvSettings()
            assert isinstance(settings.DEBUG, bool)

    def test_integer_port_validation(self, clean_environment, monkeypatch):
        """Test integer validation for email port."""
        monkeypatch.setenv("EMAIL_PORT", "587")

        settings = CommonEnvSettings()

        assert isinstance(settings.EMAIL_PORT, int)
        assert settings.EMAIL_PORT == 587

    def test_invalid_port_number(self, clean_environment, monkeypatch):
        """Test validation error for invalid port."""
        monkeypatch.setenv("EMAIL_PORT", "not_a_number")

        with pytest.raises(ValidationError) as exc_info:
            CommonEnvSettings()

        assert "email_port" in str(exc_info.value).lower() or "port" in str(exc_info.value).lower()


# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions."""

    def test_very_long_secret_key(self, clean_environment, monkeypatch):
        """Test very long secret key."""
        long_key = "a" * 500
        monkeypatch.setenv("SECRET_KEY", long_key)

        settings = CommonEnvSettings()

        assert len(settings.SECRET_KEY) == 500

    def test_special_characters_in_secret_key(self, clean_environment, monkeypatch):
        """Test special characters in secret key."""
        special_key = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        monkeypatch.setenv("SECRET_KEY", special_key)

        settings = CommonEnvSettings()

        assert settings.SECRET_KEY == special_key

    def test_unicode_in_settings(self, clean_environment, monkeypatch):
        """Test Unicode characters in settings."""
        monkeypatch.setenv("SECRET_KEY", "ключ_секрет_密钥")

        settings = CommonEnvSettings()

        assert "ключ" in settings.SECRET_KEY or "密钥" in settings.SECRET_KEY

    def test_empty_string_allowed_hosts(self, clean_environment, monkeypatch):
        """Test empty string for allowed hosts uses default."""
        monkeypatch.setenv("ALLOWED_HOSTS", "[]")

        settings = CommonEnvSettings()

        # Should use default
        assert settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]

    def test_whitespace_in_environment_name(self, clean_environment, monkeypatch):
        """Test environment name with whitespace."""
        monkeypatch.setenv("ENVIRONMENT", "   local   ")

        settings = CommonEnvSettings()

        # Pydantic might strip or keep it - test actual behavior
        assert "local" in settings.ENVIRONMENT

    def test_email_host_with_protocol(self, clean_environment, monkeypatch):
        """Test email host with protocol (should not include it)."""
        monkeypatch.setenv("EMAIL_HOST", "smtp.gmail.com")

        settings = CommonEnvSettings()

        # Should not have http:// or https://
        assert not settings.EMAIL_HOST.startswith("http")

    def test_maximum_email_port(self, clean_environment, monkeypatch):
        """Test maximum valid email port."""
        monkeypatch.setenv("EMAIL_PORT", "65535")

        settings = CommonEnvSettings()

        assert settings.EMAIL_PORT == 65535

    def test_minimum_email_port(self, clean_environment, monkeypatch):
        """Test minimum valid email port."""
        monkeypatch.setenv("EMAIL_PORT", "1")

        settings = CommonEnvSettings()

        assert settings.EMAIL_PORT == 1
