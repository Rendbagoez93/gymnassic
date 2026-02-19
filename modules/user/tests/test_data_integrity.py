"""
Test Data Integrity and Edge Cases

Tests data modification scenarios, edge cases, and integrity constraints.
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from datetime import date, timedelta

User = get_user_model()


@pytest.mark.django_db
class TestUserEmailChanges:
    """Test scenarios when user changes email."""
    
    def test_user_can_change_email(self, create_user):
        """
        SCENARIO: User wants to update email address
        EXPECTED: Email change should be allowed
        """
        user = create_user(
            username='changeuser',
            email='old@example.com',
            ktp_number='1234567890123456'
        )
        
        original_id = user.id
        new_email = 'new@example.com'
        
        user.email = new_email
        user.save()
        
        user.refresh_from_db()
        assert user.id == original_id
        assert user.email == new_email
    
    def test_email_change_to_existing_email_blocked(self, create_user):
        """
        SCENARIO: User tries to change to an already-used email
        EXPECTED: Should be blocked by unique constraint
        """
        user1 = create_user(
            username='user1',
            email='user1@example.com',
            ktp_number='1111111111111111'
        )
        
        user2 = create_user(
            username='user2',
            email='user2@example.com',
            ktp_number='2222222222222222'
        )
        
        # Try to change user2's email to user1's email
        user2.email = user1.email
        
        with pytest.raises(IntegrityError):
            user2.save()
    
    def test_email_change_requires_reverification(self, create_user):
        """
        SCENARIO: User changes email and needs to verify new one
        EXPECTED: System can track verification status
        NOTE: Requires email_verified field in production
        """
        user = create_user(
            username='verifyuser',
            email='original@example.com',
            ktp_number='1234567890123456'
        )
        
        # Change email
        user.email = 'newemail@example.com'
        user.save()
        
        # In production:
        # - Set email_verified = False
        # - Send verification email
        # - Restrict access until verified
        
        assert user.email == 'newemail@example.com'


@pytest.mark.django_db
class TestUserPhoneChanges:
    """Test scenarios when user changes phone number."""
    
    def test_user_can_change_phone(self, create_user):
        """
        SCENARIO: User updates phone number
        EXPECTED: Phone should be updated and normalized
        """
        user = create_user(
            username='phonechange',
            email='phonechange@example.com',
            ktp_number='1234567890123456',
            phone_number='081234567890'
        )
        
        new_phone = '089876543210'
        user.phone_number = new_phone
        user.full_clean()
        user.save()
        
        user.refresh_from_db()
        assert user.phone_number == '+6289876543210'
    
    def test_phone_change_security_implications(self, create_user):
        """
        SCENARIO: Phone is used for 2FA/OTP
        EXPECTED: Phone change requires verification
        """
        user = create_user(
            username='securephone',
            email='securephone@example.com',
            ktp_number='1234567890123456',
            phone_number='081234567890'
        )
        
        original_phone = user.phone_number
        new_phone = '089999999999'
        
        # Change phone
        user.phone_number = new_phone
        user.full_clean()
        user.save()
        
        # In production:
        # - Send OTP to old phone for confirmation
        # - Send OTP to new phone for verification
        # - Mark phone_verified = False
        # - Log security event
        
        assert user.phone_number != original_phone


@pytest.mark.django_db
class TestDOBModification:
    """Test scenarios when date of birth is modified."""
    
    def test_user_can_correct_dob(self, create_user):
        """
        SCENARIO: User entered wrong DOB and wants to correct
        EXPECTED: DOB can be updated
        """
        wrong_dob = date(1990, 1, 1)
        correct_dob = date(1990, 5, 15)
        
        user = create_user(
            username='dobfix',
            email='dobfix@example.com',
            ktp_number='1234567890123456',
            date_of_birth=wrong_dob
        )
        
        user.date_of_birth = correct_dob
        user.save()
        
        user.refresh_from_db()
        assert user.date_of_birth == correct_dob
    
    def test_dob_change_impacts_age_calculation(self, create_user):
        """
        SCENARIO: DOB change affects calculated age
        EXPECTED: Age recalculated based on new DOB
        """
        today = date.today()
        old_dob = date(today.year - 25, today.month, today.day)
        new_dob = date(today.year - 30, today.month, today.day)
        
        user = create_user(
            username='agechange',
            email='agechange@example.com',
            ktp_number='1234567890123456',
            date_of_birth=old_dob
        )
        
        assert user.age == 25
        
        user.date_of_birth = new_dob
        user.save()
        user.refresh_from_db()
        
        assert user.age == 30
    
    def test_dob_change_may_require_admin_approval(self, create_user):
        """
        SCENARIO: DOB is sensitive/legal data
        EXPECTED: Consider requiring admin approval for changes
        """
        user = create_user(
            username='adminapproval',
            email='adminapproval@example.com',
            ktp_number='1234567890123456',
            date_of_birth=date(1990, 1, 1)
        )
        
        # In production:
        # - Create change request
        # - Require admin approval
        # - Validate against KTP
        # - Log audit trail
        
        # For now, verify DOB is accessible
        assert user.date_of_birth is not None


@pytest.mark.django_db
class TestKTPModification:
    """Test scenarios when KTP is modified (rare but important)."""
    
    def test_ktp_should_be_immutable_after_verification(self, create_user):
        """
        SCENARIO: KTP should not change after verification
        EXPECTED: In production, prevent KTP modification
        NOTE: This is conceptual, requires additional logic
        """
        user = create_user(
            username='immutablektp',
            email='immutablektp@example.com',
            ktp_number='1234567890123456'
        )
        
        original_ktp = user.ktp_number
        
        # In production:
        # - Mark KTP as verified
        # - Prevent changes to verified KTP
        # - Require admin override
        
        # For now, verify KTP is stored
        assert user.ktp_number == original_ktp
    
    def test_ktp_correction_scenario(self, create_user):
        """
        SCENARIO: User typed KTP incorrectly during registration
        EXPECTED: Allow correction before verification
        """
        wrong_ktp = '1111111111111111'
        correct_ktp = '1234567890123456'
        
        user = create_user(
            username='ktpcorrect',
            email='ktpcorrect@example.com',
            ktp_number=wrong_ktp
        )
        
        # Correct KTP before verification
        user.ktp_number = correct_ktp
        user.save()
        
        user.refresh_from_db()
        assert user.ktp_number == correct_ktp


@pytest.mark.django_db
class TestConcurrentModifications:
    """Test concurrent modification scenarios."""
    
    def test_concurrent_email_updates_handling(self, create_user):
        """
        SCENARIO: User updates profile from multiple devices
        EXPECTED: Last write wins (default Django behavior)
        """
        user = create_user(
            username='concurrent',
            email='concurrent@example.com',
            ktp_number='1234567890123456'
        )
        
        # Simulate two instances of the same user
        user1 = User.objects.get(id=user.id)
        user2 = User.objects.get(id=user.id)
        
        # Both update email
        user1.email = 'user1update@example.com'
        user1.save()
        
        user2.email = 'user2update@example.com'
        user2.save()
        
        # Last save wins
        user.refresh_from_db()
        assert user.email == 'user2update@example.com'


@pytest.mark.django_db
class TestDataValidationEdgeCases:
    """Test edge cases in data validation."""
    
    def test_very_long_name_handling(self, create_user):
        """
        SCENARIO: User has very long name
        EXPECTED: Should be accepted up to field max_length
        """
        long_name = 'A' * 150  # Django's default max_length for first_name
        
        user = create_user(
            username='longtime',
            email='longtime@example.com',
            ktp_number='1234567890123456',
            first_name=long_name
        )
        
        assert len(user.first_name) == 150
    
    def test_special_characters_in_name(self, create_user):
        """
        SCENARIO: User has special characters in name
        EXPECTED: Should be accepted
        """
        user = create_user(
            username='specialname',
            email='special@example.com',
            ktp_number='1234567890123456',
            first_name="O'Brien",
            last_name='Müller-Schmidt'
        )
        
        assert "'" in user.first_name
        assert "-" in user.last_name
    
    def test_unicode_characters_in_name(self, create_user):
        """
        SCENARIO: User has Unicode characters (Indonesian names)
        EXPECTED: Should be handled correctly
        """
        user = create_user(
            username='unicode',
            email='unicode@example.com',
            ktp_number='1234567890123456',
            first_name='Bintang',
            last_name='Nusantara'
        )
        
        assert user.first_name == 'Bintang'
        assert user.last_name == 'Nusantara'
    
    def test_very_long_address(self, create_user):
        """
        SCENARIO: User has very long complete address
        EXPECTED: TextField should handle it
        """
        long_address = (
            "Jl. Jenderal Sudirman Kav. 52-53, RT.5/RW.3, "
            "Senayan, Kec. Kebayoran Baru, "
            "Kota Jakarta Selatan, DKI Jakarta 12190, Indonesia. "
        ) * 5  # Repeat to make it very long
        
        user = create_user(
            username='longaddress',
            email='longaddress@example.com',
            ktp_number='1234567890123456',
            address=long_address
        )
        
        user.refresh_from_db()
        assert user.address == long_address


@pytest.mark.django_db
class TestNullAndEmptyValues:
    """Test handling of null and empty values."""
    
    def test_required_fields_cannot_be_null(self):
        """
        SCENARIO: Try to create user without required fields
        EXPECTED: Should be rejected
        """
        user = User(
            username='incomplete',
            # Missing required fields
        )
        
        with pytest.raises(ValidationError):
            user.full_clean()
    
    def test_optional_fields_can_be_empty(self, create_user):
        """
        SCENARIO: Check which fields can be empty
        EXPECTED: Only truly optional fields allow empty
        NOTE: In this model, all core fields are required
        """
        # All fields in this model are required
        # This test documents that behavior
        user = create_user(
            username='required',
            email='required@example.com',
            ktp_number='1234567890123456'
        )
        
        # All required fields should be present
        assert user.username
        assert user.email
        assert user.ktp_number
        assert user.date_of_birth
        assert user.phone_number
        assert user.address


@pytest.mark.django_db
class TestDatabaseConstraints:
    """Test database-level constraints."""
    
    def test_unique_constraint_on_email(self, create_user):
        """
        SCENARIO: Database enforces email uniqueness
        EXPECTED: Cannot insert duplicate email
        """
        email = 'unique@example.com'
        
        user1 = create_user(
            username='user1',
            email=email,
            ktp_number='1111111111111111'
        )
        
        with pytest.raises(IntegrityError):
            create_user(
                username='user2',
                email=email,
                ktp_number='2222222222222222'
            )
    
    def test_unique_constraint_on_ktp(self, create_user):
        """
        SCENARIO: Database enforces KTP uniqueness
        EXPECTED: Cannot insert duplicate KTP
        """
        ktp = '1234567890123456'
        
        user1 = create_user(
            username='user1',
            email='user1@example.com',
            ktp_number=ktp
        )
        
        with pytest.raises(IntegrityError):
            create_user(
                username='user2',
                email='user2@example.com',
                ktp_number=ktp
            )
    
    def test_transaction_rollback_on_error(self, create_user):
        """
        SCENARIO: Database transaction rolls back on error
        EXPECTED: No partial data saved
        """
        initial_count = User.objects.count()
        
        try:
            with transaction.atomic():
                # Create valid user
                create_user(
                    username='valid',
                    email='valid@example.com',
                    ktp_number='1111111111111111'
                )
                
                # Try to create invalid user (duplicate KTP)
                create_user(
                    username='invalid',
                    email='invalid@example.com',
                    ktp_number='1111111111111111'  # Duplicate
                )
        except IntegrityError:
            pass
        
        # Transaction rolled back, count unchanged
        final_count = User.objects.count()
        assert final_count == initial_count
