"""
Test suite for gym configuration system.

Tests cover:
- Address model validation
- SocialMedia model validation
- OpeningHours model and time validation
- GymProfile complete validation
- GymConfigLoader file operations
- Configuration loading and caching
- Real-world scenarios for gym management
"""

import json
import tempfile
from pathlib import Path
import pytest
from pydantic import ValidationError
import yaml

from config.settings.gymconf import (
    Address,
    SocialMedia,
    OpeningHours,
    GymProfile,
    GymConfigLoader,
    load_gym_config,
    get_gym_config,
)


# ============================================================================
# ADDRESS MODEL TESTS
# ============================================================================

class TestAddressModel:
    """Test Address model for Indonesian address format."""

    def test_valid_address(self):
        """Test creating valid address."""
        address = Address(
            street_name="Jalan Sudirman No. 123",
            district_subdistrict="Senayan",
            city="Jakarta Selatan",
            province="DKI Jakarta"
        )
        
        assert address.street_name == "Jalan Sudirman No. 123"
        assert address.district_subdistrict == "Senayan"
        assert address.city == "Jakarta Selatan"
        assert address.province == "DKI Jakarta"

    def test_address_missing_required_field(self):
        """Test address validation fails with missing required fields."""
        with pytest.raises(ValidationError):
            Address(
                street_name="Jalan Test",
                city="Jakarta",
                # Missing district_subdistrict and province
            )

    def test_address_empty_string_not_allowed(self):
        """Test address fields cannot be empty strings."""
        with pytest.raises(ValidationError):
            Address(
                street_name="",  # Empty string
                district_subdistrict="Test",
                city="Jakarta",
                province="DKI Jakarta"
            )

    def test_address_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError):
            Address(
                street_name="Jalan Test",
                district_subdistrict="Test",
                city="Jakarta",
                province="DKI Jakarta",
                postal_code="12345"  # Extra field
            )

    def test_multiple_indonesian_addresses(self, sample_addresses):
        """Test creating multiple Indonesian addresses."""
        for addr_data in sample_addresses:
            address = Address(**addr_data)
            assert address.street_name
            assert address.district_subdistrict
            assert address.city
            assert address.province


# ============================================================================
# SOCIAL MEDIA MODEL TESTS
# ============================================================================

class TestSocialMediaModel:
    """Test SocialMedia model."""

    def test_valid_social_media(self):
        """Test creating valid social media handles."""
        social = SocialMedia(
            instagram="@gymnassic_fitness",
            x="@gymnassic",
            facebook="GymnaissicFitnessCenter"
        )
        
        assert social.instagram == "@gymnassic_fitness"
        assert social.x == "@gymnassic"
        assert social.facebook == "GymnaissicFitnessCenter"

    def test_social_media_missing_field(self):
        """Test social media requires all three platforms."""
        with pytest.raises(ValidationError):
            SocialMedia(
                instagram="@test",
                x="@test",
                # Missing facebook
            )

    def test_social_media_extra_fields_forbidden(self):
        """Test extra fields not allowed."""
        with pytest.raises(ValidationError):
            SocialMedia(
                instagram="@test",
                x="@test",
                facebook="test",
                tiktok="@test"  # Extra field
            )

    def test_social_media_without_at_symbol(self):
        """Test social media handles can be without @ symbol."""
        social = SocialMedia(
            instagram="gymnassic_fitness",
            x="gymnassic",
            facebook="GymnaissicFitnessCenter"
        )
        
        assert social.instagram == "gymnassic_fitness"


# ============================================================================
# OPENING HOURS MODEL TESTS
# ============================================================================

class TestOpeningHoursModel:
    """Test OpeningHours model and validation."""

    def test_valid_opening_hours(self):
        """Test creating valid opening hours."""
        hours = OpeningHours(start="06:00", end="21:00")
        
        assert hours.start == "06:00"
        assert hours.end == "21:00"

    def test_opening_hours_invalid_time_format(self):
        """Test invalid time format is rejected."""
        with pytest.raises(ValidationError):
            OpeningHours(start="6:00", end="21:00")  # Missing leading zero
        
        with pytest.raises(ValidationError):
            OpeningHours(start="06:00", end="25:00")  # Invalid hour
        
        with pytest.raises(ValidationError):
            OpeningHours(start="06:00", end="21:60")  # Invalid minute

    def test_opening_hours_end_before_start(self):
        """Test end time must be after start time."""
        with pytest.raises(ValidationError) as exc_info:
            OpeningHours(start="21:00", end="06:00")
        
        assert "end time must be after start time" in str(exc_info.value).lower()

    def test_opening_hours_same_time_invalid(self):
        """Test start and end cannot be the same time."""
        with pytest.raises(ValidationError):
            OpeningHours(start="09:00", end="09:00")

    def test_opening_hours_early_morning_to_evening(self):
        """Test typical gym hours."""
        hours = OpeningHours(start="05:00", end="23:00")
        assert hours.start == "05:00"
        assert hours.end == "23:00"

    def test_opening_hours_24_hour_format_validation(self):
        """Test 24-hour format is strictly enforced."""
        # Valid 24-hour times
        valid_times = [
            ("00:00", "23:59"),
            ("06:30", "22:45"),
            ("07:15", "20:30"),
        ]
        
        for start, end in valid_times:
            hours = OpeningHours(start=start, end=end)
            assert hours.start == start
            assert hours.end == end


# ============================================================================
# GYM PROFILE MODEL TESTS
# ============================================================================

class TestGymProfileModel:
    """Test complete GymProfile model."""

    def test_valid_gym_profile(self, valid_gym_config_data):
        """Test creating valid gym profile."""
        profile = GymProfile(**valid_gym_config_data)
        
        assert profile.gym_name == "Gymnassic Fitness Center"
        assert profile.address.city == "Jakarta Selatan"
        assert len(profile.phone_numbers) == 2
        assert profile.email == "info@gymnassic.co.id"
        assert profile.social_media.instagram == "@gymnassic_fitness"
        assert len(profile.opening_days) == 7
        assert profile.opening_hours.start == "06:00"

    def test_gym_profile_missing_required_fields(self, invalid_gym_config_missing_required):
        """Test gym profile requires all fields."""
        with pytest.raises(ValidationError):
            GymProfile(**invalid_gym_config_missing_required)

    def test_gym_profile_invalid_email(self, invalid_gym_config_bad_email):
        """Test gym profile validates email format."""
        with pytest.raises(ValidationError) as exc_info:
            GymProfile(**invalid_gym_config_bad_email)
        
        # Check that email validation failed
        errors = exc_info.value.errors()
        email_errors = [e for e in errors if e['loc'][0] == 'email']
        assert len(email_errors) > 0

    def test_gym_profile_invalid_opening_hours(self, invalid_opening_hours):
        """Test gym profile validates opening hours."""
        with pytest.raises(ValidationError) as exc_info:
            GymProfile(**invalid_opening_hours)
        
        assert "end time must be after start time" in str(exc_info.value).lower()

    def test_gym_profile_phone_number_validation(self):
        """Test phone number format validation."""
        valid_data = {
            "gym_name": "Test Gym",
            "address": {
                "street_name": "Test St",
                "district_subdistrict": "Test",
                "city": "Test City",
                "province": "Test Province",
            },
            "phone_numbers": ["+62 21 5551234", "021-5551234", "(021) 555-1234"],
            "email": "test@test.com",
            "social_media": {"instagram": "@test", "x": "@test", "facebook": "test"},
            "opening_days": ["Monday", "Tuesday"],
            "opening_hours": {"start": "09:00", "end": "17:00"},
        }
        
        profile = GymProfile(**valid_data)
        assert len(profile.phone_numbers) == 3

    def test_gym_profile_invalid_phone_number(self):
        """Test invalid phone number formats are rejected."""
        invalid_data = {
            "gym_name": "Test Gym",
            "address": {
                "street_name": "Test St",
                "district_subdistrict": "Test",
                "city": "Test City",
                "province": "Test Province",
            },
            "phone_numbers": ["invalid-phone@number"],  # Contains @
            "email": "test@test.com",
            "social_media": {"instagram": "@test", "x": "@test", "facebook": "test"},
            "opening_days": ["Monday"],
            "opening_hours": {"start": "09:00", "end": "17:00"},
        }
        
        with pytest.raises(ValidationError) as exc_info:
            GymProfile(**invalid_data)
        
        assert "Invalid phone number" in str(exc_info.value)

    def test_gym_profile_unique_opening_days(self):
        """Test opening days must be unique."""
        data = {
            "gym_name": "Test Gym",
            "address": {
                "street_name": "Test St",
                "district_subdistrict": "Test",
                "city": "Test City",
                "province": "Test Province",
            },
            "phone_numbers": ["+62 123456789"],
            "email": "test@test.com",
            "social_media": {"instagram": "@test", "x": "@test", "facebook": "test"},
            "opening_days": ["Monday", "Tuesday", "Monday"],  # Duplicate
            "opening_hours": {"start": "09:00", "end": "17:00"},
        }
        
        with pytest.raises(ValidationError) as exc_info:
            GymProfile(**data)
        
        assert "unique" in str(exc_info.value).lower()

    def test_gym_profile_valid_days_only(self):
        """Test only valid day names are accepted."""
        data = {
            "gym_name": "Test Gym",
            "address": {
                "street_name": "Test St",
                "district_subdistrict": "Test",
                "city": "Test City",
                "province": "Test Province",
            },
            "phone_numbers": ["+62 123456789"],
            "email": "test@test.com",
            "social_media": {"instagram": "@test", "x": "@test", "facebook": "test"},
            "opening_days": ["Monday", "InvalidDay"],  # Invalid day
            "opening_hours": {"start": "09:00", "end": "17:00"},
        }
        
        with pytest.raises(ValidationError):
            GymProfile(**data)

    def test_gym_profile_minimum_one_opening_day(self):
        """Test at least one opening day is required."""
        data = {
            "gym_name": "Test Gym",
            "address": {
                "street_name": "Test St",
                "district_subdistrict": "Test",
                "city": "Test City",
                "province": "Test Province",
            },
            "phone_numbers": ["+62 123456789"],
            "email": "test@test.com",
            "social_media": {"instagram": "@test", "x": "@test", "facebook": "test"},
            "opening_days": [],  # Empty list
            "opening_hours": {"start": "09:00", "end": "17:00"},
        }
        
        with pytest.raises(ValidationError):
            GymProfile(**data)


# ============================================================================
# GYM CONFIG LOADER TESTS
# ============================================================================

class TestGymConfigLoader:
    """Test GymConfigLoader class."""

    def test_loader_default_paths(self):
        """Test loader uses default paths when not specified."""
        loader = GymConfigLoader()
        
        assert loader.config_path.name == "gym_profile.yaml"
        assert loader.schema_path.name == "gym_schema.json"

    def test_loader_custom_paths(self, tmp_path):
        """Test loader accepts custom paths."""
        custom_config = tmp_path / "custom_gym.yaml"
        custom_schema = tmp_path / "custom_schema.json"
        
        loader = GymConfigLoader(
            config_path=custom_config,
            schema_path=custom_schema
        )
        
        assert loader.config_path == custom_config
        assert loader.schema_path == custom_schema

    def test_load_schema_success(self, temp_gym_schema_file):
        """Test loading valid schema file."""
        loader = GymConfigLoader(schema_path=temp_gym_schema_file)
        schema = loader.load_schema()
        
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_load_schema_file_not_found(self, tmp_path):
        """Test loading non-existent schema file."""
        non_existent = tmp_path / "non_existent.json"
        loader = GymConfigLoader(schema_path=non_existent)
        
        with pytest.raises(FileNotFoundError):
            loader.load_schema()

    def test_load_config_success(self, temp_gym_yaml_file):
        """Test loading valid YAML config file."""
        loader = GymConfigLoader(config_path=temp_gym_yaml_file)
        config = loader.load_config()
        
        assert isinstance(config, dict)
        assert "gym_name" in config
        assert "address" in config

    def test_load_config_file_not_found(self, tmp_path):
        """Test loading non-existent config file."""
        non_existent = tmp_path / "non_existent.yaml"
        loader = GymConfigLoader(config_path=non_existent)
        
        with pytest.raises(FileNotFoundError):
            loader.load_config()

    def test_load_and_validate_success(self, temp_gym_yaml_file, temp_gym_schema_file):
        """Test loading and validating valid configuration."""
        loader = GymConfigLoader(
            config_path=temp_gym_yaml_file,
            schema_path=temp_gym_schema_file
        )
        
        profile = loader.load_and_validate()
        
        assert isinstance(profile, GymProfile)
        assert profile.gym_name == "Gymnassic Fitness Center"

    def test_load_and_validate_invalid_config(self, tmp_path, temp_gym_schema_file):
        """Test loading invalid configuration raises validation error."""
        # Create invalid YAML
        invalid_yaml = tmp_path / "invalid.yaml"
        with open(invalid_yaml, "w") as f:
            yaml.dump({"gym_name": "Test"}, f)  # Missing required fields
        
        loader = GymConfigLoader(
            config_path=invalid_yaml,
            schema_path=temp_gym_schema_file
        )
        
        with pytest.raises(ValueError) as exc_info:
            loader.load_and_validate()
        
        assert "validation failed" in str(exc_info.value).lower()


# ============================================================================
# MODULE FUNCTIONS TESTS
# ============================================================================

class TestModuleFunctions:
    """Test module-level functions for loading gym config."""

    def test_load_gym_config_with_valid_file(self, temp_gym_yaml_file, monkeypatch):
        """Test load_gym_config function with valid configuration."""
        # Monkeypatch the BASE_DIR to use our temp file
        from config.settings import gymconf
        
        loader = GymConfigLoader(config_path=temp_gym_yaml_file)
        monkeypatch.setattr(gymconf, "gym_config_loader", loader)
        
        profile = load_gym_config()
        
        assert isinstance(profile, GymProfile)
        assert profile.gym_name == "Gymnassic Fitness Center"

    def test_get_gym_config_caching(self, temp_gym_yaml_file, monkeypatch):
        """Test get_gym_config caches the configuration."""
        from config.settings import gymconf
        
        loader = GymConfigLoader(config_path=temp_gym_yaml_file)
        monkeypatch.setattr(gymconf, "gym_config_loader", loader)
        
        # Clear cache if it exists
        if hasattr(get_gym_config, "_cached_config"):
            delattr(get_gym_config, "_cached_config")
        
        # First call should load
        profile1 = get_gym_config()
        
        # Second call should return cached
        profile2 = get_gym_config()
        
        # Should be the same instance (cached)
        assert profile1 is profile2


# ============================================================================
# REAL-WORLD SCENARIO TESTS
# ============================================================================

@pytest.mark.integration
class TestRealWorldScenarios:
    """Test real-world gym configuration scenarios."""

    def test_24_7_gym_configuration(self):
        """Test 24/7 gym that's open all week."""
        # Note: Opening hours still need start < end per day
        # 24/7 would typically be handled differently in production
        config = {
            "gym_name": "Fitness 24/7",
            "address": {
                "street_name": "Jalan Gatot Subroto No. 88",
                "district_subdistrict": "Kuningan",
                "city": "Jakarta Selatan",
                "province": "DKI Jakarta",
            },
            "phone_numbers": ["+62 21 5551111"],
            "email": "info@fitness247.co.id",
            "social_media": {
                "instagram": "@fitness247",
                "x": "@fitness247",
                "facebook": "Fitness247Indonesia",
            },
            "opening_days": [
                "Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"
            ],
            "opening_hours": {"start": "00:00", "end": "23:59"},
        }
        
        profile = GymProfile(**config)
        assert len(profile.opening_days) == 7

    def test_boutique_gym_limited_hours(self):
        """Test boutique gym with limited operating hours."""
        config = {
            "gym_name": "Elite Fitness Studio",
            "address": {
                "street_name": "Jalan Kemang Raya No. 45",
                "district_subdistrict": "Bangka",
                "city": "Jakarta Selatan",
                "province": "DKI Jakarta",
            },
            "phone_numbers": ["+62 21 7191234", "+62 878 9999 1234"],
            "email": "contact@elitefitness.id",
            "social_media": {
                "instagram": "@elite_fitness_jkt",
                "x": "@elitefitness",
                "facebook": "EliteFitnessJakarta",
            },
            "opening_days": ["Monday", "Wednesday", "Friday"],
            "opening_hours": {"start": "06:00", "end": "12:00"},
        }
        
        profile = GymProfile(**config)
        assert len(profile.opening_days) == 3
        assert profile.opening_hours.start == "06:00"

    def test_gym_chain_multiple_contacts(self):
        """Test gym chain with multiple contact numbers."""
        config = {
            "gym_name": "Gold's Gym Indonesia",
            "address": {
                "street_name": "Pacific Place Mall, SCBD Lot 3-5",
                "district_subdistrict": "Senayan",
                "city": "Jakarta Selatan",
                "province": "DKI Jakarta",
            },
            "phone_numbers": [
                "+62 21 57901234",
                "+62 21 57905678",
                "+62 812 1234 5678",
                "(021) 5790-1234"
            ],
            "email": "info@goldsgym.co.id",
            "social_media": {
                "instagram": "@goldsgymindonesia",
                "x": "@goldsgymid",
                "facebook": "GoldsGymIndonesia",
            },
            "opening_days": [
                "Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday"
            ],
            "opening_hours": {"start": "05:00", "end": "23:00"},
        }
        
        profile = GymProfile(**config)
        assert len(profile.phone_numbers) == 4

    def test_gym_with_indonesian_email_domain(self):
        """Test gym with .co.id domain (Indonesian)."""
        config = {
            "gym_name": "Fitness First Indonesia",
            "address": {
                "street_name": "Grand Indonesia Shopping Town",
                "district_subdistrict": "Menteng",
                "city": "Jakarta Pusat",
                "province": "DKI Jakarta",
            },
            "phone_numbers": ["+62 21 23581234"],
            "email": "member.services@fitnessfirst.co.id",
            "social_media": {
                "instagram": "@fitnessfirstindonesia",
                "x": "@ffitnessfirst",
                "facebook": "FitnessFirstIndonesia",
            },
            "opening_days": [
                "Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday"
            ],
            "opening_hours": {"start": "06:00", "end": "22:00"},
        }
        
        profile = GymProfile(**config)
        assert profile.email.endswith(".co.id")
        assert profile.address.city == "Jakarta Pusat"
