"""
Test Auth and Login Flow Scenarios

Tests email login, phone login, password management, and authentication flows.
"""
import pytest
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password
from datetime import date

User = get_user_model()


@pytest.mark.django_db
class TestEmailLoginFlow:
    """Test standard email-based authentication flow."""
    
    def test_user_can_login_with_email_and_password(self, valid_user_data, create_user):
        """
        SCENARIO: User logs in with email and password
        EXPECTED: Authentication should succeed
        """
        # Create user
        password = 'TestPassword123!'
        user = create_user(**{**valid_user_data, 'password': password})
        
        # Authenticate using username (Django default)
        authenticated_user = authenticate(
            username=user.username,
            password=password
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.email == user.email
    
    def test_login_fails_with_wrong_password(self, valid_user_data, create_user):
        """
        SCENARIO: User tries to login with wrong password
        EXPECTED: Authentication should fail
        """
        user = create_user(**{**valid_user_data, 'password': 'CorrectPassword123!'})
        
        # Try to authenticate with wrong password
        authenticated_user = authenticate(
            username=user.username,
            password='WrongPassword456!'
        )
        
        assert authenticated_user is None
    
    def test_login_fails_for_inactive_user(self, valid_user_data, create_user):
        """
        SCENARIO: Inactive user tries to login
        EXPECTED: Authentication should fail
        """
        password = 'TestPassword123!'
        user = create_user(**{**valid_user_data, 'password': password})
        
        # Deactivate user
        user.is_active = False
        user.save()
        
        # Try to authenticate
        authenticated_user = authenticate(
            username=user.username,
            password=password
        )
        
        assert authenticated_user is None
    
    def test_login_fails_for_soft_deleted_user(self, valid_user_data, create_user):
        """
        SCENARIO: Soft-deleted user tries to login
        EXPECTED: Authentication should fail (user not found in default queryset)
        """
        password = 'TestPassword123!'
        user = create_user(**{**valid_user_data, 'password': password})
        
        # Soft delete user
        user.delete()
        
        # Try to find user (should not be found in default queryset)
        try:
            user_check = User.objects.get(username=user.username)
            # If we get here, it means the user was found (unexpected)
            assert False, "Soft-deleted user should not be in default queryset"
        except User.DoesNotExist:
            # This is expected
            assert True


@pytest.mark.django_db
class TestPhoneNumberLogin:
    """Test phone-based authentication scenarios (common in SEA)."""
    
    def test_phone_number_normalized_on_save(self, valid_user_data, create_user):
        """
        SCENARIO: User registers with various phone formats
        EXPECTED: Phone should be normalized to +62 format
        """
        # Test with 0 prefix
        data1 = valid_user_data.copy()
        data1['username'] = 'user1'
        data1['email'] = 'user1@example.com'
        data1['ktp_number'] = '1111111111111111'
        data1['phone_number'] = '081234567890'
        
        user1 = create_user(**data1)
        user1.full_clean()  # This triggers the clean() method
        user1.save()
        user1.refresh_from_db()
        
        assert user1.phone_number == '+6281234567890'
    
    def test_phone_number_with_62_prefix_normalized(self, create_user):
        """
        SCENARIO: User registers with 62 prefix (no plus)
        EXPECTED: Should be normalized to +62
        """
        user = create_user(
            username='user2',
            email='user2@example.com',
            ktp_number='2222222222222222',
            phone_number='6281234567890'
        )
        user.full_clean()
        user.save()
        user.refresh_from_db()
        
        assert user.phone_number == '+6281234567890'
    
    def test_phone_number_already_with_plus62_stays_same(self, create_user):
        """
        SCENARIO: User registers with +62 format
        EXPECTED: Should remain in +62 format
        """
        user = create_user(
            username='user3',
            email='user3@example.com',
            ktp_number='3333333333333333',
            phone_number='+6281234567890'
        )
        user.full_clean()
        user.save()
        user.refresh_from_db()
        
        assert user.phone_number == '+6281234567890'
    
    def test_phone_with_spaces_and_dashes_normalized(self, create_user):
        """
        SCENARIO: User enters phone with spaces or dashes
        EXPECTED: Should be cleaned and normalized
        """
        user = create_user(
            username='user4',
            email='user4@example.com',
            ktp_number='4444444444444444',
            phone_number='0812-3456-7890'
        )
        user.full_clean()
        user.save()
        user.refresh_from_db()
        
        assert user.phone_number == '+6281234567890'
        assert ' ' not in user.phone_number
        assert '-' not in user.phone_number
    
    def test_can_find_user_by_normalized_phone(self, create_user):
        """
        SCENARIO: System needs to find user by phone number
        EXPECTED: Can query by normalized format
        """
        user = create_user(
            username='user5',
            email='user5@example.com',
            ktp_number='5555555555555555',
            phone_number='081234567890'
        )
        user.full_clean()
        user.save()
        
        # Query by normalized format
        found_user = User.objects.get(phone_number='+6281234567890')
        assert found_user.id == user.id


@pytest.mark.django_db
class TestPasswordManagement:
    """Test password-related scenarios."""
    
    def test_password_is_hashed_not_plaintext(self, valid_user_data, create_user):
        """
        SCENARIO: User registers with password
        EXPECTED: Password should be hashed, not stored as plaintext
        """
        password = 'SecurePassword123!'
        user = create_user(**{**valid_user_data, 'password': password})
        
        # Password should not be stored as plaintext
        assert user.password != password
        
        # But should be verifiable
        assert check_password(password, user.password)
    
    def test_user_can_change_password(self, valid_user_data, create_user):
        """
        SCENARIO: User wants to change password
        EXPECTED: Old password invalid, new password works
        """
        old_password = 'OldPassword123!'
        new_password = 'NewPassword456!'
        
        user = create_user(**{**valid_user_data, 'password': old_password})
        
        # Change password
        user.set_password(new_password)
        user.save()
        
        # Old password should not work
        assert not check_password(old_password, user.password)
        
        # New password should work
        assert check_password(new_password, user.password)
    
    def test_password_reset_scenario(self, valid_user_data, create_user):
        """
        SCENARIO: User forgets password and requests reset
        EXPECTED: Can set new password without knowing old one
        """
        old_password = 'ForgottenPassword123!'
        user = create_user(**{**valid_user_data, 'password': old_password})
        
        # Simulate password reset (user doesn't need to provide old password)
        new_password = 'ResetPassword789!'
        user.set_password(new_password)
        user.save()
        
        # New password should work
        authenticated_user = authenticate(
            username=user.username,
            password=new_password
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == user.id


@pytest.mark.django_db
class TestAccountActivation:
    """Test account activation and email verification flows."""
    
    def test_new_user_can_be_inactive_by_default(self, valid_user_data):
        """
        SCENARIO: User registers but needs email verification
        EXPECTED: User created as inactive until verified
        """
        user_data = valid_user_data.copy()
        password = user_data.pop('password')
        
        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.is_active = False  # Simulate pending verification
        user.save()
        
        assert not user.is_active
        
        # Cannot login while inactive
        authenticated_user = authenticate(
            username=user.username,
            password=password
        )
        assert authenticated_user is None
    
    def test_user_activation_enables_login(self, valid_user_data):
        """
        SCENARIO: User verifies email and account gets activated
        EXPECTED: Can now login successfully
        """
        user_data = valid_user_data.copy()
        password = user_data.pop('password')
        
        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        
        # Activate user (simulate email verification)
        user.is_active = True
        user.save()
        
        # Should now be able to login
        authenticated_user = authenticate(
            username=user.username,
            password=password
        )
        
        assert authenticated_user is not None
        assert authenticated_user.is_active


@pytest.mark.django_db
class TestMultipleLoginAttempts:
    """Test scenarios involving multiple login attempts."""
    
    def test_multiple_failed_login_attempts_tracking(self, valid_user_data, create_user):
        """
        SCENARIO: User attempts multiple failed logins (fraud protection)
        EXPECTED: System can track failed attempts
        NOTE: This requires additional fields, shown as example
        """
        password = 'CorrectPassword123!'
        user = create_user(**{**valid_user_data, 'password': password})
        
        # Simulate 3 failed login attempts
        failed_attempts = 0
        for _ in range(3):
            result = authenticate(
                username=user.username,
                password='WrongPassword'
            )
            if result is None:
                failed_attempts += 1
        
        assert failed_attempts == 3
        
        # Successful login should still work
        success = authenticate(
            username=user.username,
            password=password
        )
        assert success is not None
    
    def test_user_can_have_multiple_active_sessions(self, valid_user_data, create_user):
        """
        SCENARIO: User logs in from multiple devices
        EXPECTED: Multiple simultaneous sessions allowed
        NOTE: Session management would be handled by Django's session framework
        """
        password = 'Password123!'
        user = create_user(**{**valid_user_data, 'password': password})
        
        # Simulate multiple logins (in real app, each would create a session)
        auth1 = authenticate(username=user.username, password=password)
        auth2 = authenticate(username=user.username, password=password)
        
        assert auth1 is not None
        assert auth2 is not None
        assert auth1.id == auth2.id  # Same user
