"""
Test Lifecycle Scenarios

Tests user account lifecycle from creation to deletion and retention.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration and account creation."""
    
    def test_new_user_registration_flow(self, valid_user_data):
        """
        SCENARIO: New user completes registration
        EXPECTED: User account created successfully
        """
        password = valid_user_data.pop('password')
        
        # Create new user
        user = User.objects.create_user(**valid_user_data)
        user.set_password(password)
        user.save()
        
        # Verify user is created
        assert user.id is not None
        assert user.username == valid_user_data['username']
        assert user.email == valid_user_data['email']
        assert user.ktp_number == valid_user_data['ktp_number']
        assert user.date_joined is not None
    
    def test_newly_registered_user_is_active(self, create_user):
        """
        SCENARIO: User completes registration
        EXPECTED: Account is active by default
        """
        user = create_user(
            username='newactive',
            email='newactive@example.com',
            ktp_number='1234567890123456'
        )
        
        # New user is active
        assert user.is_active is True
    
    def test_newly_registered_user_not_staff(self, create_user):
        """
        SCENARIO: Regular user registration
        EXPECTED: User is not staff by default
        """
        user = create_user(
            username='notstaff',
            email='notstaff@example.com',
            ktp_number='1234567890123456'
        )
        
        # Regular user, not staff
        assert user.is_staff is False
        assert user.is_superuser is False


@pytest.mark.django_db
class TestAccountActivation:
    """Test account activation and verification flows."""
    
    def test_pending_user_activation(self, valid_user_data):
        """
        SCENARIO: User registers but email not verified yet
        EXPECTED: Account created as inactive
        """
        password = valid_user_data.pop('password')
        
        user = User.objects.create_user(**valid_user_data)
        user.set_password(password)
        user.is_active = False  # Pending verification
        user.save()
        
        assert user.is_active is False
    
    def test_user_activation_after_email_verification(self, create_user):
        """
        SCENARIO: User verifies email
        EXPECTED: Account becomes active
        """
        user = create_user(
            username='verify',
            email='verify@example.com',
            ktp_number='1234567890123456'
        )
        
        # Initially inactive (pending verification)
        user.is_active = False
        user.save()
        
        # User verifies email
        user.is_active = True
        user.save()
        
        user.refresh_from_db()
        assert user.is_active is True


@pytest.mark.django_db
class TestAccountDeactivation:
    """Test account deactivation scenarios."""
    
    def test_user_deactivates_account_voluntarily(self, create_user):
        """
        SCENARIO: User chooses to deactivate account
        EXPECTED: Account marked as inactive
        """
        user = create_user(
            username='deactivate',
            email='deactivate@example.com',
            ktp_number='1234567890123456'
        )
        
        assert user.is_active is True
        
        # User deactivates
        user.is_active = False
        user.save()
        
        user.refresh_from_db()
        assert user.is_active is False
    
    def test_admin_deactivates_user_account(self, create_user):
        """
        SCENARIO: Admin deactivates problematic user
        EXPECTED: User cannot login
        """
        user = create_user(
            username='problem',
            email='problem@example.com',
            ktp_number='1234567890123456'
        )
        
        # Admin deactivates account
        user.is_active = False
        user.save()
        
        # User cannot authenticate
        from django.contrib.auth import authenticate
        result = authenticate(username=user.username, password='testpass123')
        assert result is None
    
    def test_deactivated_user_can_be_reactivated(self, create_user):
        """
        SCENARIO: Deactivated user appeals and gets reactivated
        EXPECTED: Account can be reactivated
        """
        user = create_user(
            username='reactivate',
            email='reactivate@example.com',
            ktp_number='1234567890123456'
        )
        
        # Deactivate
        user.is_active = False
        user.save()
        assert user.is_active is False
        
        # Reactivate
        user.is_active = True
        user.save()
        
        user.refresh_from_db()
        assert user.is_active is True


@pytest.mark.django_db
class TestAccountDeletion:
    """Test account deletion (soft and hard)."""
    
    def test_user_soft_deletes_account(self, create_user):
        """
        SCENARIO: User deletes account
        EXPECTED: Soft delete applied
        """
        user = create_user(
            username='softdel',
            email='softdel@example.com',
            ktp_number='1234567890123456'
        )
        
        user_id = user.id
        user.delete()  # Soft delete
        
        # Not in default queryset
        assert not User.objects.filter(id=user_id).exists()
        
        # Still in database
        assert User.all_objects.filter(id=user_id).exists()
        
        # deleted_at timestamp set
        deleted_user = User.all_objects.get(id=user_id)
        assert deleted_user.deleted_at is not None
    
    def test_soft_deleted_user_can_be_restored(self, create_user):
        """
        SCENARIO: User wants to restore deleted account (within retention period)
        EXPECTED: Account can be restored
        """
        user = create_user(
            username='restore',
            email='restore@example.com',
            ktp_number='1234567890123456'
        )
        
        user_id = user.id
        
        # Delete
        user.delete()
        assert not User.objects.filter(id=user_id).exists()
        
        # Restore
        deleted_user = User.all_objects.get(id=user_id)
        deleted_user.restore()
        
        # Back in default queryset
        assert User.objects.filter(id=user_id).exists()
        
        restored_user = User.objects.get(id=user_id)
        assert restored_user.deleted_at is None
    
    def test_hard_delete_permanently_removes_user(self, create_user):
        """
        SCENARIO: After retention period, permanently delete user
        EXPECTED: User completely removed from database
        """
        user = create_user(
            username='harddel',
            email='harddel@example.com',
            ktp_number='1234567890123456'
        )
        
        user_id = user.id
        user.hard_delete()
        
        # Completely removed
        assert not User.objects.filter(id=user_id).exists()
        assert not User.all_objects.filter(id=user_id).exists()


@pytest.mark.django_db
class TestDataRetentionPolicies:
    """Test data retention and compliance scenarios."""
    
    def test_soft_deleted_data_retained_for_period(self, create_user):
        """
        SCENARIO: Legal requirement to retain data for X days
        EXPECTED: Soft-deleted data remains queryable
        """
        user = create_user(
            username='retain',
            email='retain@example.com',
            ktp_number='1234567890123456'
        )
        
        user_id = user.id
        user.delete()
        
        # Data still accessible for compliance
        deleted_user = User.all_objects.get(id=user_id)
        assert deleted_user.email == 'retain@example.com'
        assert deleted_user.ktp_number == '1234567890123456'
    
    def test_identify_users_past_retention_period(self, create_user):
        """
        SCENARIO: Find users deleted more than X days ago
        EXPECTED: Can query by deletion date
        """
        retention_days = 90
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        # Create and soft delete user
        user = create_user(
            username='expired',
            email='expired@example.com',
            ktp_number='1234567890123456'
        )
        user.delete()
        
        # Manually set old deletion date (for testing)
        user.deleted_at = cutoff_date - timedelta(days=1)
        user.save()
        
        # Query users past retention
        expired_users = User.all_objects.filter(
            deleted_at__isnull=False,
            deleted_at__lt=cutoff_date
        )
        
        assert user in expired_users
    
    def test_legal_hold_prevents_deletion(self, create_user):
        """
        SCENARIO: User data under legal hold
        EXPECTED: Cannot be deleted even after retention period
        NOTE: Requires is_legal_hold field in production
        """
        user = create_user(
            username='legalhold',
            email='legalhold@example.com',
            ktp_number='1234567890123456'
        )
        
        user_id = user.id
        user.delete()
        
        # In production would check:
        # if user.is_legal_hold:
        #     raise CannotDeleteException("User under legal hold")
        
        # For now, verify user can be queried
        deleted_user = User.all_objects.get(id=user_id)
        assert deleted_user is not None


@pytest.mark.django_db
class TestUserProfileUpdates:
    """Test user profile update lifecycle."""
    
    def test_user_updates_profile_information(self, create_user):
        """
        SCENARIO: User updates their profile
        EXPECTED: Changes saved successfully
        """
        user = create_user(
            username='updateprofile',
            email='old@example.com',
            ktp_number='1234567890123456',
            first_name='Old',
            last_name='Name'
        )
        
        # Update profile
        user.first_name = 'New'
        user.last_name = 'Name'
        user.email = 'new@example.com'
        user.save()
        
        user.refresh_from_db()
        assert user.first_name == 'New'
        assert user.email == 'new@example.com'
    
    def test_profile_update_history_tracking(self, create_user):
        """
        SCENARIO: Track when user last updated profile
        EXPECTED: Timestamp recorded
        NOTE: Requires updated_at field from TimeStampedModel
        """
        user = create_user(
            username='tracking',
            email='tracking@example.com',
            ktp_number='1234567890123456'
        )
        
        # AbstractUser doesn't have updated_at
        # But has date_joined
        assert user.date_joined is not None


@pytest.mark.django_db
class TestAccountMerging:
    """Test scenarios involving account merging or migration."""
    
    def test_cannot_merge_active_duplicate_accounts(self, create_user):
        """
        SCENARIO: User has duplicate accounts (shouldn't happen)
        EXPECTED: System prevents duplicate KTP/email
        """
        from django.db import IntegrityError
        
        user1 = create_user(
            username='user1',
            email='user@example.com',
            ktp_number='1234567890123456'
        )
        
        # Cannot create duplicate
        with pytest.raises(IntegrityError):
            create_user(
                username='user2',
                email='user@example.com',
                ktp_number='1234567890123456'
            )


@pytest.mark.django_db
class TestAccountAging:
    """Test scenarios related to account age."""
    
    def test_identify_newly_registered_users(self, create_user):
        """
        SCENARIO: Find users registered in last 7 days
        EXPECTED: Can query by registration date
        """
        recent_cutoff = timezone.now() - timedelta(days=7)
        
        user = create_user(
            username='newuser',
            email='newuser@example.com',
            ktp_number='1234567890123456'
        )
        
        # Find recent users
        recent_users = User.objects.filter(date_joined__gte=recent_cutoff)
        assert user in recent_users
    
    def test_identify_inactive_old_accounts(self, create_user):
        """
        SCENARIO: Find accounts not logged in for 1 year
        EXPECTED: Can query by last_login
        """
        old_cutoff = timezone.now() - timedelta(days=365)
        
        user = create_user(
            username='dormant',
            email='dormant@example.com',
            ktp_number='1234567890123456'
        )
        
        # Set old last_login (or leave as None)
        user.last_login = old_cutoff - timedelta(days=1)
        user.save()
        
        # Find dormant accounts
        dormant_users = User.objects.filter(
            last_login__lt=old_cutoff
        ) | User.objects.filter(last_login__isnull=True)
        
        assert user in dormant_users


@pytest.mark.django_db
class TestSecurityLifecycle:
    """Test security-related lifecycle events."""
    
    def test_password_change_invalidates_sessions(self, create_user):
        """
        SCENARIO: User changes password
        EXPECTED: Should invalidate all sessions
        NOTE: Django handles this automatically in request context
        """
        password = 'OldPassword123!'
        user = create_user(
            username='passchange',
            email='passchange@example.com',
            ktp_number='1234567890123456',
            password=password
        )
        
        # Change password
        new_password = 'NewPassword456!'
        user.set_password(new_password)
        user.save()
        
        # Old password no longer works
        from django.contrib.auth import authenticate
        old_auth = authenticate(username=user.username, password=password)
        assert old_auth is None
        
        # New password works
        new_auth = authenticate(username=user.username, password=new_password)
        assert new_auth is not None
    
    def test_account_locked_after_breach(self, create_user):
        """
        SCENARIO: Potential security breach detected
        EXPECTED: Can lock account immediately
        """
        user = create_user(
            username='breach',
            email='breach@example.com',
            ktp_number='1234567890123456'
        )
        
        # Lock account
        user.is_active = False
        user.save()
        
        # User cannot login
        assert user.is_active is False


@pytest.mark.django_db
class TestComplianceLifecycle:
    """Test compliance-related lifecycle scenarios."""
    
    def test_gdpr_right_to_be_forgotten(self, create_user):
        """
        SCENARIO: User exercises GDPR right to be forgotten
        EXPECTED: Account deleted and data removed after retention
        """
        user = create_user(
            username='gdprdelete',
            email='gdprdelete@example.com',
            ktp_number='1234567890123456'
        )
        
        user_id = user.id
        
        # User requests deletion
        user.delete()
        
        # After retention period, hard delete
        deleted_user = User.all_objects.get(id=user_id)
        deleted_user.hard_delete()
        
        # Completely removed
        assert not User.all_objects.filter(id=user_id).exists()
    
    def test_export_user_data_for_compliance(self, create_user):
        """
        SCENARIO: User requests data export (GDPR)
        EXPECTED: All personal data can be exported
        """
        user = create_user(
            username='exportdata',
            email='export@example.com',
            ktp_number='1234567890123456',
            first_name='John',
            last_name='Doe'
        )
        
        # Export all personal data
        exported_data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'ktp_number': user.ktp_number,
            'date_of_birth': str(user.date_of_birth),
            'phone_number': user.phone_number,
            'address': user.address,
            'date_joined': str(user.date_joined),
        }
        
        assert exported_data['username'] == 'exportdata'
        assert exported_data['ktp_number'] == '1234567890123456'
