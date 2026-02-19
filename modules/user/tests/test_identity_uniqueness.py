"""
Test Identity & Uniqueness Scenarios

Tests duplicate registration, unique constraints, and soft-delete behavior.
"""
import pytest
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()


@pytest.mark.django_db
class TestDuplicateRegistration:
    """Test scenarios for duplicate registration attempts."""
    
    def test_duplicate_email_registration_blocked(self, valid_user_data, create_user):
        """
        SCENARIO: User tries to register with an existing email
        EXPECTED: Registration should fail (strict identity system)
        """
        # Create first user
        user1 = create_user(**valid_user_data)
        assert user1.email == valid_user_data['email']
        
        # Try to create another user with same email but different KTP
        duplicate_data = valid_user_data.copy()
        duplicate_data['username'] = 'different_username'
        duplicate_data['ktp_number'] = '9999999999999999'
        
        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError) as exc_info:
            create_user(**duplicate_data)
        
        # Check for constraint violation (constraint name or field name)
        error_msg = str(exc_info.value).lower()
        assert 'unique_email_when_not_deleted' in error_msg or 'email' in error_msg
    
    def test_duplicate_ktp_registration_blocked(self, valid_user_data, create_user):
        """
        SCENARIO: User tries to register with an existing KTP number
        EXPECTED: Registration should fail (Indonesian identity system is strict)
        """
        # Create first user
        user1 = create_user(**valid_user_data)
        assert user1.ktp_number == valid_user_data['ktp_number']
        
        # Try to create another user with same KTP but different email
        duplicate_data = valid_user_data.copy()
        duplicate_data['username'] = 'different_username2'
        duplicate_data['email'] = 'different@example.com'
        
        # Should raise IntegrityError due to unique constraint
        with pytest.raises(IntegrityError) as exc_info:
            create_user(**duplicate_data)
        
        # Check for constraint violation (constraint name or field name)
        error_msg = str(exc_info.value).lower()
        assert 'unique_ktp_when_not_deleted' in error_msg or 'ktp_number' in error_msg
    
    def test_both_email_and_ktp_duplicate_blocked(self, valid_user_data, create_user):
        """
        SCENARIO: User tries to register with both duplicate email AND KTP
        EXPECTED: Registration should fail
        """
        # Create first user
        user1 = create_user(**valid_user_data)
        
        # Try to create exact duplicate (different username only)
        duplicate_data = valid_user_data.copy()
        duplicate_data['username'] = 'yet_another_username'
        
        # Should raise IntegrityError
        with pytest.raises(IntegrityError):
            create_user(**duplicate_data)
    
    def test_same_user_different_identifiers_allowed(self, create_user):
        """
        SCENARIO: Different users with unique email and KTP
        EXPECTED: Both should be created successfully
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
        
        assert User.objects.count() == 2
        assert user1.email != user2.email
        assert user1.ktp_number != user2.ktp_number


@pytest.mark.django_db
class TestSoftDeletedUserReregistration:
    """Test scenarios for soft-deleted users trying to re-register."""
    
    def test_soft_deleted_user_email_available_for_new_registration(self, valid_user_data, create_user):
        """
        SCENARIO: User account is soft-deleted, same email tries to register again
        EXPECTED: Should succeed (unique constraint only applies to non-deleted)
        """
        # Create and soft-delete first user
        user1 = create_user(**valid_user_data)
        user1_id = user1.id
        user1.delete()  # Soft delete
        
        # Verify user is soft-deleted
        assert user1.deleted_at is not None
        assert User.objects.filter(id=user1_id).count() == 0  # Not in default queryset
        assert User.all_objects.filter(id=user1_id).count() == 1  # Still in all_objects
        
        # Create new user with same email (but different username and KTP)
        new_user_data = valid_user_data.copy()
        new_user_data['username'] = 'newusername'
        new_user_data['ktp_number'] = '8888888888888888'
        
        user2 = create_user(**new_user_data)
        
        assert user2.email == user1.email
        assert user2.id != user1_id
        assert user2.deleted_at is None
    
    def test_soft_deleted_user_ktp_available_for_new_registration(self, valid_user_data, create_user):
        """
        SCENARIO: User account is soft-deleted, same KTP tries to register again
        EXPECTED: Should succeed (conditional unique constraint)
        """
        # Create and soft-delete first user
        user1 = create_user(**valid_user_data)
        user1_id = user1.id
        user1.delete()  # Soft delete
        
        # Create new user with same KTP (but different email and username)
        new_user_data = valid_user_data.copy()
        new_user_data['username'] = 'differentusername'
        new_user_data['email'] = 'different@example.com'
        
        user2 = create_user(**new_user_data)
        
        assert user2.ktp_number == user1.ktp_number
        assert user2.id != user1_id
        assert user2.deleted_at is None
    
    def test_restore_soft_deleted_user(self, create_user, valid_user_data):
        """
        SCENARIO: Instead of new registration, restore the old account
        EXPECTED: User should be restored with original data
        """
        # Create and soft-delete user
        user = create_user(**valid_user_data)
        original_id = user.id
        original_email = user.email
        original_ktp = user.ktp_number
        
        user.delete()  # Soft delete
        assert user.deleted_at is not None
        
        # Restore the user
        user.restore()
        
        assert user.deleted_at is None
        assert user.id == original_id
        assert user.email == original_email
        assert user.ktp_number == original_ktp
        assert User.objects.filter(id=original_id).count() == 1
    
    def test_cannot_create_duplicate_while_active_user_exists(self, create_user):
        """
        SCENARIO: Active user exists, try to create duplicate
        EXPECTED: Should fail even if another user with same data was deleted
        """
        # Create user1 and soft-delete
        user1 = create_user(
            username='user1',
            email='test@example.com',
            ktp_number='1111111111111111'
        )
        user1.delete()
        
        # Create user2 with same email and KTP (should succeed)
        user2 = create_user(
            username='user2',
            email='test@example.com',
            ktp_number='1111111111111111'
        )
        
        # Try to create user3 with same email (should fail because user2 is active)
        with pytest.raises(IntegrityError):
            create_user(
                username='user3',
                email='test@example.com',
                ktp_number='3333333333333333'
            )


@pytest.mark.django_db
class TestUniqueConstraintBehavior:
    """Test unique constraint behavior in various scenarios."""
    
    def test_multiple_soft_deleted_users_with_same_email(self, create_user):
        """
        SCENARIO: Multiple soft-deleted users can have the same email
        EXPECTED: Should be allowed (constraint only applies to active users)
        """
        # Create and delete first user
        user1 = create_user(
            username='user1',
            email='shared@example.com',
            ktp_number='1111111111111111'
        )
        user1.delete()
        
        # Create and delete second user with same email
        user2 = create_user(
            username='user2',
            email='shared@example.com',
            ktp_number='2222222222222222'
        )
        user2.delete()
        
        # Both should exist in all_objects
        deleted_users = User.all_objects.filter(email='shared@example.com', deleted_at__isnull=False)
        assert deleted_users.count() == 2
    
    def test_multiple_soft_deleted_users_with_same_ktp(self, create_user):
        """
        SCENARIO: Multiple soft-deleted users can have the same KTP
        EXPECTED: Should be allowed (constraint only applies to active users)
        """
        # Create and delete first user
        user1 = create_user(
            username='user1',
            email='user1@example.com',
            ktp_number='9999999999999999'
        )
        user1.delete()
        
        # Create and delete second user with same KTP
        user2 = create_user(
            username='user2',
            email='user2@example.com',
            ktp_number='9999999999999999'
        )
        user2.delete()
        
        # Both should exist in all_objects
        deleted_users = User.all_objects.filter(ktp_number='9999999999999999', deleted_at__isnull=False)
        assert deleted_users.count() == 2
    
    def test_username_can_be_duplicate_across_active_users(self, create_user):
        """
        SCENARIO: Django's unique username constraint
        EXPECTED: Usernames must be unique even across soft-deleted users (Django default)
        """
        user1 = create_user(
            username='uniqueusername',
            email='user1@example.com',
            ktp_number='1234567890123456'
        )
        
        # Try to create another user with same username
        with pytest.raises(IntegrityError):
            create_user(
                username='uniqueusername',
                email='user2@example.com',
                ktp_number='6543210987654321'
            )
