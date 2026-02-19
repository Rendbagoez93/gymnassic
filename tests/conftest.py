"""
Pytest configuration and fixtures for the Gymnassic project.

This module provides:
- Django test configuration
- Database fixtures with temporary test database
- Test data factories and fixtures
- Environment configuration fixtures
- Gym configuration fixtures
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
import json
import pytest
import yaml
from django.conf import settings
from django.core.management import call_command
from faker import Faker


# Configure Django settings for testing
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
os.environ.setdefault("DJANGO_ENV", "local")
os.environ.setdefault("ENV", "local")

# Initialize Django
if not settings.configured:
    django.setup()


# Initialize Faker
fake = Faker()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """
    Set up test database for the entire test session.
    Uses in-memory SQLite database for speed.
    """
    # Add tests app to INSTALLED_APPS so test models are created
    if 'tests' not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['tests']
    
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": False,
        "TEST": {
            "NAME": ":memory:",
        },
    }
    
    # Run migrations at session level, outside of any transaction
    with django_db_blocker.unblock():
        from django.db import connection
        from django.core.management import call_command as django_call_command
        connection.set_autocommit(True)
        
        # First run migrations for all existing apps
        call_command("migrate", "--run-syncdb", verbosity=0)
        
        # Create tables for test models
        from django.db import connection
        from tests import models as test_models
        
        with connection.schema_editor() as schema_editor:
            try:
                schema_editor.create_model(test_models.ConcreteBaseModel)
            except Exception:
                pass  # Table already exists
            
            try:
                schema_editor.create_model(test_models.ConcreteTimeStampedModel)
            except Exception:
                pass  # Table already exists
            
            try:
                schema_editor.create_model(test_models.ConcreteSoftDeleteModel)
            except Exception:
                pass  # Table already exists
            
            try:
                schema_editor.create_model(test_models.ConcreteSoftDeleteableModel)
            except Exception:
                pass  # Table already exists


@pytest.fixture(scope="function")
def db_fixture(django_db_setup, django_db_blocker):
    """
    Provide a clean database for each test function.
    """
    with django_db_blocker.unblock():
        yield
        call_command("flush", "--no-input", verbosity=0)


# ============================================================================
# ENVIRONMENT SETTINGS FIXTURES
# ============================================================================

@pytest.fixture
def temp_env_file():
    """
    Create a temporary .env file for testing.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("secret_key=test-secret-key-12345678\n")
        f.write("debug=true\n")
        f.write("allowed_hosts=localhost,testserver\n")
        f.write("database_engine=django.db.backends.sqlite3\n")
        f.write("database_name=test_db.sqlite3\n")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def local_env_data():
    """
    Sample local environment configuration data.
    """
    return {
        "secret_key": "local-secret-key-for-testing",
        "debug": True,
        "allowed_hosts": "localhost,127.0.0.1,0.0.0.0",
        "environment": "local",
        "timezone": "Asia/Jakarta",
        "language_code": "en-us",
    }


@pytest.fixture
def development_env_data(local_env_data):
    """
    Alias for local_env_data for backward compatibility.
    """
    return local_env_data


@pytest.fixture
def production_env_data():
    """
    Sample production environment configuration data.
    """
    return {
        "secret_key": "prod-secret-key-for-testing-very-secure",
        "debug": False,
        "allowed_hosts": "example.com,www.example.com",
        "environment": "production",
        "timezone": "Asia/Jakarta",
        "language_code": "id-id",
        "email_backend": "django.core.mail.backends.smtp.EmailBackend",
        "email_host": "smtp.example.com",
        "email_port": 587,
        "email_use_tls": True,
        "email_host_user": "user@example.com",
        "email_host_password": "password123",
    }


@pytest.fixture
def local_db_data():
    """
    Sample local database configuration data.
    """
    return {
        "environment": "local",
        "database_engine": "django.db.backends.sqlite3",
        "database_name": "db.sqlite3",
    }


@pytest.fixture
def production_db_data():
    """
    Sample production database configuration data.
    """
    return {
        "environment": "production",
        "database_engine": "django.db.backends.postgresql",
        "database_name": "gymnassic_prod",
        "database_user": "dbuser",
        "database_password": "dbpass123",
        "database_host": "localhost",
        "database_port": "5432",
        "database_conn_max_age": 600,
        "database_conn_health_checks": True,
    }


# ============================================================================
# GYM CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def valid_gym_config_data():
    """
    Valid gym configuration data for testing.
    """
    return {
        "gym_name": "Gymnassic Fitness Center",
        "address": {
            "street_name": "Jalan Sudirman No. 123",
            "district_subdistrict": "Senayan",
            "city": "Jakarta Selatan",
            "province": "DKI Jakarta",
        },
        "phone_numbers": ["+62 21 5551234", "+62 812 3456 7890"],
        "email": "info@gymnassic.co.id",
        "social_media": {
            "instagram": "@gymnassic_fitness",
            "x": "@gymnassic",
            "facebook": "GymnaissicFitnessCenter",
        },
        "opening_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "opening_hours": {
            "start": "06:00",
            "end": "21:00",
        },
    }


@pytest.fixture
def invalid_gym_config_missing_required():
    """
    Invalid gym configuration with missing required fields.
    """
    return {
        "gym_name": "Test Gym",
        "address": {
            "street_name": "Test Street",
            "city": "Test City",
            # Missing district_subdistrict and province
        },
    }


@pytest.fixture
def invalid_gym_config_bad_email():
    """
    Invalid gym configuration with invalid email format.
    """
    return {
        "gym_name": "Test Gym",
        "address": {
            "street_name": "Test Street",
            "district_subdistrict": "Test District",
            "city": "Test City",
            "province": "Test Province",
        },
        "phone_numbers": ["+62 123456789"],
        "email": "not-a-valid-email",  # Invalid email
        "social_media": {
            "instagram": "@test",
            "x": "@test",
            "facebook": "test",
        },
        "opening_days": ["Monday"],
        "opening_hours": {
            "start": "09:00",
            "end": "17:00",
        },
    }


@pytest.fixture
def invalid_opening_hours():
    """
    Invalid gym configuration with end time before start time.
    """
    return {
        "gym_name": "Test Gym",
        "address": {
            "street_name": "Test Street",
            "district_subdistrict": "Test District",
            "city": "Test City",
            "province": "Test Province",
        },
        "phone_numbers": ["+62 123456789"],
        "email": "test@example.com",
        "social_media": {
            "instagram": "@test",
            "x": "@test",
            "facebook": "test",
        },
        "opening_days": ["Monday"],
        "opening_hours": {
            "start": "21:00",
            "end": "06:00",  # End before start
        },
    }


@pytest.fixture
def temp_gym_yaml_file(valid_gym_config_data):
    """
    Create a temporary gym_profile.yaml file for testing.
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(valid_gym_config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_gym_schema_file():
    """
    Create a temporary gym_schema.json file for testing.
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Gym Profile Schema",
        "type": "object",
        "properties": {
            "gym_name": {"type": "string", "minLength": 1},
            "address": {"type": "object"},
            "phone_numbers": {"type": "array"},
            "email": {"type": "string"},
            "social_media": {"type": "object"},
            "opening_days": {"type": "array"},
            "opening_hours": {"type": "object"},
        },
        "required": ["gym_name", "address", "phone_numbers", "email", "social_media", "opening_days", "opening_hours"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# ============================================================================
# TEST DATA FACTORIES
# ============================================================================

@pytest.fixture
def sample_addresses():
    """
    Generate sample Indonesian addresses for testing.
    """
    return [
        {
            "street_name": "Jalan Thamrin No. 45",
            "district_subdistrict": "Menteng",
            "city": "Jakarta Pusat",
            "province": "DKI Jakarta",
        },
        {
            "street_name": "Jalan Asia Afrika No. 100",
            "district_subdistrict": "Sumur Bandung",
            "city": "Bandung",
            "province": "Jawa Barat",
        },
        {
            "street_name": "Jalan Malioboro No. 56",
            "district_subdistrict": "Gondomanan",
            "city": "Yogyakarta",
            "province": "DI Yogyakarta",
        },
    ]


@pytest.fixture
def sample_phone_numbers():
    """
    Generate sample Indonesian phone numbers for testing.
    """
    return [
        "+62 21 5551234",
        "+62 812 3456 7890",
        "+62 22 8765432",
        "021-5551234",
        "(021) 555-1234",
    ]


@pytest.fixture
def sample_emails():
    """
    Generate sample email addresses for testing.
    """
    return [
        "info@gymnassic.co.id",
        "admin@fitness-center.com",
        "contact@gym24.id",
        "support@healthclub.net",
    ]


@pytest.fixture
def sample_social_media():
    """
    Generate sample social media handles for testing.
    """
    return [
        {
            "instagram": "@gymnassic_fitness",
            "x": "@gymnassic",
            "facebook": "GymnaissicFitnessCenter",
        },
        {
            "instagram": "@fitness_center_id",
            "x": "@fitnesscenter",
            "facebook": "FitnessCenterIndonesia",
        },
    ]


# ============================================================================
# DATABASE URL PARSING FIXTURES
# ============================================================================

@pytest.fixture
def sample_database_urls():
    """
    Sample database URLs for testing parsing logic.
    """
    return {
        "sqlite_relative": "sqlite:///db.sqlite3",
        "sqlite_absolute": "sqlite:////absolute/path/to/db.sqlite3",
        "sqlite_memory": "sqlite:///:memory:",
        "postgresql_full": "postgresql://user:password@localhost:5432/dbname",
        "postgresql_minimal": "postgresql://localhost/dbname",
        "postgres_alias": "postgres://user:pass@host:5432/db",
    }


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def clean_environment():
    """
    Ensure clean environment variables for testing.
    """
    original_env = os.environ.copy()
    # Clear test-related environment variables
    test_vars = [
        "DJANGO_ENV", "ENV",
        "secret_key", "debug", "allowed_hosts", "environment",
        "database_engine", "database_name", "database_user",
        "database_password", "database_host", "database_port",
        "timezone", "language_code", "static_url", "media_url",
        "email_backend", "email_host", "email_port"
    ]
    for var in test_vars:
        os.environ.pop(var, None)
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_base_dir(tmp_path):
    """
    Create a temporary base directory structure for testing.
    """
    # Create directory structure
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings").mkdir()
    (tmp_path / "shared").mkdir()
    (tmp_path / "applications").mkdir()
    (tmp_path / "tests").mkdir()
    return tmp_path


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# ============================================================================
# SESSION-SCOPED FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def faker_instance():
    """
    Provide a Faker instance for generating test data.
    """
    return Faker(["id_ID", "en_US"])  # Indonesian and English locales
