"""
Shared fixtures for user module tests.

Provides reusable test data and fixtures for all user model tests.
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def valid_user_data():
    """Basic valid user data for registration."""
    return {
        'username': 'johndoe',
        'email': 'john.doe@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'ktp_number': '1234567890123456',
        'date_of_birth': date(1990, 5, 15),
        'address': 'Jl. Sudirman No. 123, Jakarta Pusat, DKI Jakarta 10110',
        'phone_number': '081234567890',
        'password': 'SecurePass123!'
    }


@pytest.fixture
def alternative_user_data():
    """Alternative user data for duplicate testing."""
    return {
        'username': 'janedoe',
        'email': 'jane.doe@example.com',
        'first_name': 'Jane',
        'last_name': 'Doe',
        'ktp_number': '6543210987654321',
        'date_of_birth': date(1992, 8, 20),
        'address': 'Jl. Thamrin No. 456, Jakarta Pusat, DKI Jakarta 10230',
        'phone_number': '082345678901',
        'password': 'AnotherPass456!'
    }


@pytest.fixture
def minor_user_data():
    """User data for a minor (under 18 years old)."""
    today = date.today()
    dob_minor = date(today.year - 16, today.month, today.day)
    
    return {
        'username': 'teenuser',
        'email': 'teen.user@example.com',
        'first_name': 'Teen',
        'last_name': 'User',
        'ktp_number': '1111222233334444',
        'date_of_birth': dob_minor,
        'address': 'Jl. Pemuda No. 789, Jakarta Selatan, DKI Jakarta 12345',
        'phone_number': '083456789012',
        'password': 'TeenPass789!'
    }


@pytest.fixture
def adult_user_data():
    """User data for an adult (over 18 years old)."""
    today = date.today()
    dob_adult = date(today.year - 25, today.month, today.day)
    
    return {
        'username': 'adultuser',
        'email': 'adult.user@example.com',
        'first_name': 'Adult',
        'last_name': 'User',
        'ktp_number': '5555666677778888',
        'date_of_birth': dob_adult,
        'address': 'Jl. Veteran No. 321, Jakarta Timur, DKI Jakarta 13450',
        'phone_number': '084567890123',
        'password': 'AdultPass321!'
    }


@pytest.fixture
def elderly_user_data():
    """User data for an elderly user (over 60 years old)."""
    today = date.today()
    dob_elderly = date(today.year - 65, today.month, today.day)
    
    return {
        'username': 'elderlyuser',
        'email': 'elderly.user@example.com',
        'first_name': 'Elderly',
        'last_name': 'User',
        'ktp_number': '9999888877776666',
        'date_of_birth': dob_elderly,
        'address': 'Jl. Proklamasi No. 567, Jakarta Pusat, DKI Jakarta 10320',
        'phone_number': '085678901234',
        'password': 'ElderlyPass567!'
    }


@pytest.fixture
def phone_number_variations():
    """Different phone number format variations for normalization testing."""
    return {
        'with_zero': '081234567890',
        'with_62': '6281234567890',
        'with_plus62': '+6281234567890',
        'with_spaces': '0812 3456 7890',
        'with_dashes': '0812-3456-7890',
        'international': '+62 812-3456-7890'
    }


@pytest.fixture
def invalid_phone_numbers():
    """Invalid phone number formats."""
    return [
        '12345',  # Too short
        '0812345678901234567890',  # Too long
        '+1234567890',  # Wrong country code
        'abcdefghijk',  # Letters
        '0912345678',  # Invalid prefix (09 not used in Indonesia)
    ]


@pytest.fixture
def invalid_ktp_numbers():
    """Invalid KTP number formats."""
    return [
        '123456789012345',  # 15 digits (too short)
        '12345678901234567',  # 17 digits (too long)
        '12345678901234ab',  # Contains letters
        '1234 5678 9012 3456',  # Contains spaces
        '',  # Empty
    ]


@pytest.fixture
def create_user(db):
    """Factory fixture to create users easily."""
    def _create_user(**kwargs):
        # Set defaults if not provided
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'ktp_number': '1122334455667788',
            'date_of_birth': date(1995, 1, 1),
            'address': 'Test Address',
            'phone_number': '081234567890',
        }
        defaults.update(kwargs)
        
        # Extract password if provided
        password = defaults.pop('password', 'testpass123')
        
        # Create user
        user = User.objects.create_user(**defaults)
        user.set_password(password)
        user.save()
        
        return user
    
    return _create_user


@pytest.fixture
def create_verified_user(create_user):
    """Factory fixture to create verified users."""
    def _create_verified_user(**kwargs):
        user = create_user(**kwargs)
        user.is_active = True
        user.save()
        return user
    
    return _create_verified_user


@pytest.fixture
def sample_user(create_user):
    """A single sample user for simple tests."""
    return create_user(
        username='sampleuser',
        email='sample@example.com',
        ktp_number='1234567890123456'
    )


@pytest.fixture
def soft_deleted_user(create_user):
    """A soft-deleted user for restoration tests."""
    user = create_user(
        username='deleteduser',
        email='deleted@example.com',
        ktp_number='9876543210987654'
    )
    user.delete()  # Soft delete
    return user


@pytest.fixture
def user_with_different_phones(create_user):
    """Create multiple users with different phone formats."""
    users = []
    phone_formats = [
        '081234567890',
        '6281234567891',
        '+6281234567892',
    ]
    
    for i, phone in enumerate(phone_formats):
        user = create_user(
            username=f'phoneuser{i}',
            email=f'phone{i}@example.com',
            ktp_number=f'111122223333444{i}',
            phone_number=phone
        )
        users.append(user)
    
    return users


@pytest.fixture
def future_date():
    """A date in the future for validation testing."""
    return date.today() + timedelta(days=365)


@pytest.fixture
def past_century_date():
    """A date from over 100 years ago."""
    return date(1900, 1, 1)
