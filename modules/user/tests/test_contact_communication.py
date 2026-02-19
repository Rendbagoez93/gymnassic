"""
Test Contact & Communication Scenarios

Tests notification systems, contact validation, and communication workflows.
"""
import pytest
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()


@pytest.mark.django_db
class TestContactInformation:
    """Test contact information retrieval and management."""
    
    def test_get_contact_info_returns_all_fields(self, valid_user_data, create_user):
        """
        SCENARIO: System needs user's contact information
        EXPECTED: Should return email, phone, and address
        """
        user = create_user(**valid_user_data)
        
        contact_info = user.get_contact_info()
        
        assert 'email' in contact_info
        assert 'phone' in contact_info
        assert 'address' in contact_info
        assert contact_info['email'] == user.email
        assert contact_info['phone'] == user.phone_number
        assert contact_info['address'] == user.address
    
    def test_contact_info_accessible_for_notifications(self, create_user):
        """
        SCENARIO: System sends notifications to user
        EXPECTED: Can access all contact methods
        """
        user = create_user(
            username='notifyuser',
            email='notify@example.com',
            ktp_number='1234567890123456',
            phone_number='081234567890',
            address='Jakarta, Indonesia'
        )
        
        # Email notification target
        assert user.email is not None
        assert '@' in user.email
        
        # SMS notification target
        assert user.phone_number is not None
        
        # Physical mail target
        assert user.address is not None


@pytest.mark.django_db
class TestEmailValidation:
    """Test email validation and handling scenarios."""
    
    def test_valid_email_format_accepted(self, create_user):
        """
        SCENARIO: User registers with valid email
        EXPECTED: Email should be accepted
        """
        valid_emails = [
            'user@example.com',
            'user.name@example.com',
            'user+tag@example.co.id',
            'user_123@sub.example.com',
        ]
        
        for idx, email in enumerate(valid_emails):
            user = create_user(
                username=f'user{idx}',
                email=email,
                ktp_number=f'123456789012345{idx}'
            )
            assert user.email == email
    
    def test_invalid_email_format_validation(self):
        """
        SCENARIO: User tries to register with invalid email
        EXPECTED: Should be rejected
        """
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
            'user @example.com',
            'user@.com',
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_email(email)
    
    def test_email_case_sensitivity(self, create_user):
        """
        SCENARIO: User registers with mixed-case email
        EXPECTED: Email domain is normalized to lowercase (Django default behavior)
        NOTE: Local part (before @) preserves case, domain is lowercased
        """
        user = create_user(
            username='caseuser',
            email='User@Example.COM',
            ktp_number='1234567890123456'
        )
        
        # Django normalizes the domain part to lowercase
        assert user.email == 'User@example.com'
    
    def test_email_with_plus_addressing(self, create_user):
        """
        SCENARIO: User uses email plus addressing (gmail feature)
        EXPECTED: Should be accepted as valid
        """
        user = create_user(
            username='plususer',
            email='user+gym@example.com',
            ktp_number='1234567890123456'
        )
        
        assert '+' in user.email
        assert user.email == 'user+gym@example.com'


@pytest.mark.django_db
class TestPhoneNumberValidation:
    """Test phone number validation scenarios."""
    
    def test_valid_indonesian_phone_formats(self, phone_number_variations, create_user):
        """
        SCENARIO: User enters phone in different valid formats
        EXPECTED: All valid Indonesian formats accepted
        """
        valid_phones = [
            phone_number_variations['with_zero'],
            phone_number_variations['with_62'],
            phone_number_variations['with_plus62'],
        ]
        
        for idx, phone in enumerate(valid_phones):
            user = create_user(
                username=f'phoneuser{idx}',
                email=f'phone{idx}@example.com',
                ktp_number=f'111111111111111{idx}',
                phone_number=phone
            )
            # After normalization, should all start with +62
            user.full_clean()
            user.save()
            assert user.phone_number.startswith('+62')
    
    def test_phone_length_validation(self, create_user):
        """
        SCENARIO: Phone number length validation
        EXPECTED: Indonesian phones should be appropriate length
        """
        # Valid length (10-14 digits after +62)
        valid_phone = '+628123456789'  # 12 digits after +62
        
        user = create_user(
            username='lengthuser',
            email='length@example.com',
            ktp_number='1234567890123456',
            phone_number=valid_phone
        )
        
        assert len(user.phone_number.replace('+62', '')) >= 9
        assert len(user.phone_number.replace('+62', '')) <= 13
    
    def test_phone_invalid_country_code_rejected(self, invalid_phone_numbers):
        """
        SCENARIO: User enters non-Indonesian phone number
        EXPECTED: Should be rejected by validator
        """
        from django.core.exceptions import ValidationError
        
        # Phone with US country code
        user = User(
            username='usphone',
            email='us@example.com',
            ktp_number='1234567890123456',
            date_of_birth=date(1990, 1, 1),
            address='Address',
            phone_number='+1234567890'  # US format
        )
        
        with pytest.raises(ValidationError):
            user.full_clean()


@pytest.mark.django_db
class TestNotificationScenarios:
    """Test notification and communication scenarios."""
    
    def test_send_email_notification_simulation(self, create_user):
        """
        SCENARIO: System sends email notification to user
        EXPECTED: Email address is accessible and valid
        """
        user = create_user(
            username='emailuser',
            email='notifications@example.com',
            ktp_number='1234567890123456'
        )
        
        # Simulate email notification
        recipient_email = user.email
        assert recipient_email is not None
        
        # Validate email format
        validate_email(recipient_email)
    
    def test_send_sms_notification_simulation(self, create_user):
        """
        SCENARIO: System sends SMS to user
        EXPECTED: Phone number is normalized and ready for SMS
        """
        user = create_user(
            username='smsuser',
            email='sms@example.com',
            ktp_number='1234567890123456',
            phone_number='081234567890'
        )
        
        user.full_clean()
        user.save()
        
        # Phone should be normalized for SMS gateway
        sms_target = user.phone_number
        assert sms_target.startswith('+62')
    
    def test_multiple_notification_channels(self, create_user):
        """
        SCENARIO: System sends notification via multiple channels
        EXPECTED: Can access all communication channels
        """
        user = create_user(
            username='multiuser',
            email='multi@example.com',
            ktp_number='1234567890123456',
            phone_number='081234567890'
        )
        
        # All channels available
        contact = user.get_contact_info()
        
        assert contact['email'] is not None
        assert contact['phone'] is not None
        assert contact['address'] is not None


@pytest.mark.django_db
class TestCommunicationPreferences:
    """Test communication preferences and opt-in scenarios."""
    
    def test_user_has_email_for_communication(self, create_user):
        """
        SCENARIO: Check if user has valid email for communication
        EXPECTED: Email field is not null and valid
        """
        user = create_user(
            username='commuser',
            email='communication@example.com',
            ktp_number='1234567890123456'
        )
        
        has_email = user.email is not None and user.email != ''
        assert has_email is True
    
    def test_user_has_phone_for_communication(self, create_user):
        """
        SCENARIO: Check if user has valid phone for communication
        EXPECTED: Phone field is not null and valid
        """
        user = create_user(
            username='phonecommuser',
            email='phonecomm@example.com',
            ktp_number='1234567890123456',
            phone_number='081234567890'
        )
        
        has_phone = user.phone_number is not None and user.phone_number != ''
        assert has_phone is True


@pytest.mark.django_db
class TestContactDataIntegrity:
    """Test contact data integrity and consistency."""
    
    def test_email_remains_consistent_after_save(self, create_user):
        """
        SCENARIO: Email should not change unexpectedly
        EXPECTED: Email remains exactly as set
        """
        original_email = 'consistent@example.com'
        
        user = create_user(
            username='consistentuser',
            email=original_email,
            ktp_number='1234567890123456'
        )
        
        user.refresh_from_db()
        assert user.email == original_email
    
    def test_phone_normalized_consistently(self, create_user):
        """
        SCENARIO: Phone normalization is consistent
        EXPECTED: Same input always produces same output
        """
        phone_input = '081234567890'
        
        user1 = create_user(
            username='user1',
            email='user1@example.com',
            ktp_number='1111111111111111',
            phone_number=phone_input
        )
        user1.full_clean()
        user1.save()
        
        user2 = create_user(
            username='user2',
            email='user2@example.com',
            ktp_number='2222222222222222',
            phone_number=phone_input
        )
        user2.full_clean()
        user2.save()
        
        # Both should normalize to same format
        assert user1.phone_number == user2.phone_number == '+6281234567890'
    
    def test_address_stored_as_complete_text(self, create_user):
        """
        SCENARIO: User provides complete address
        EXPECTED: Full address stored without truncation
        """
        full_address = (
            "Jl. Jenderal Sudirman Kav. 52-53, "
            "RT.5/RW.3, Senayan, Kec. Kebayoran Baru, "
            "Kota Jakarta Selatan, DKI Jakarta 12190"
        )
        
        user = create_user(
            username='addressuser',
            email='address@example.com',
            ktp_number='1234567890123456',
            address=full_address
        )
        
        user.refresh_from_db()
        assert user.address == full_address
        assert len(user.address) == len(full_address)


@pytest.mark.django_db
class TestContactUpdateScenarios:
    """Test scenarios where users update their contact information."""
    
    def test_user_can_update_email(self, create_user):
        """
        SCENARIO: User wants to change email address
        EXPECTED: Email can be updated
        NOTE: In production, should trigger re-verification
        """
        user = create_user(
            username='updateuser',
            email='old@example.com',
            ktp_number='1234567890123456'
        )
        
        new_email = 'new@example.com'
        user.email = new_email
        user.save()
        
        user.refresh_from_db()
        assert user.email == new_email
    
    def test_user_can_update_phone(self, create_user):
        """
        SCENARIO: User wants to change phone number
        EXPECTED: Phone can be updated and normalized
        """
        user = create_user(
            username='phoneupdateuser',
            email='phoneupdate@example.com',
            ktp_number='1234567890123456',
            phone_number='081234567890'
        )
        
        new_phone = '089876543210'
        user.phone_number = new_phone
        user.full_clean()
        user.save()
        
        user.refresh_from_db()
        assert user.phone_number == '+6289876543210'
    
    def test_user_can_update_address(self, create_user):
        """
        SCENARIO: User moves and updates address
        EXPECTED: Address can be updated
        """
        user = create_user(
            username='moveuser',
            email='move@example.com',
            ktp_number='1234567890123456',
            address='Old Address, Jakarta'
        )
        
        new_address = 'New Address, Bandung'
        user.address = new_address
        user.save()
        
        user.refresh_from_db()
        assert user.address == new_address
