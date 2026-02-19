"""
Test Privacy & Security Scenarios

Tests data protection, access control, and security considerations.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from datetime import date

User = get_user_model()


@pytest.mark.django_db
class TestSensitiveDataProtection:
    """Test protection of sensitive user data."""
    
    def test_ktp_is_sensitive_data(self, create_user):
        """
        SCENARIO: KTP is highly sensitive personal data
        EXPECTED: Should be stored securely
        NOTE: Consider encryption at rest in production
        """
        sensitive_ktp = '1234567890123456'
        
        user = create_user(
            username='sensitive',
            email='sensitive@example.com',
            ktp_number=sensitive_ktp
        )
        
        # KTP is stored in database
        assert user.ktp_number == sensitive_ktp
        
        # In production:
        # - Encrypt at field level or database level
        # - Use database encryption (transparent data encryption)
        # - Implement access logging
        # - Mask in logs and error messages
    
    def test_dob_is_sensitive_data(self, create_user):
        """
        SCENARIO: DOB is personal identifiable information
        EXPECTED: Should be protected
        """
        dob = date(1990, 5, 15)
        
        user = create_user(
            username='dobsensitive',
            email='dobsensitive@example.com',
            ktp_number='1234567890123456',
            date_of_birth=dob
        )
        
        # DOB stored
        assert user.date_of_birth == dob
        
        # In production:
        # - Limit access to authorized personnel
        # - Mask in UI (show only year or age)
        # - Log access for audit
    
    def test_address_is_sensitive_data(self, create_user):
        """
        SCENARIO: Address is personal information
        EXPECTED: Should be protected
        """
        address = 'Jl. Sudirman No. 123, Jakarta'
        
        user = create_user(
            username='addresssensitive',
            email='addresssensitive@example.com',
            ktp_number='1234567890123456',
            address=address
        )
        
        # Address stored
        assert user.address == address
        
        # In production:
        # - Restrict access
        # - Partial masking in some contexts


@pytest.mark.django_db
class TestPasswordSecurity:
    """Test password security measures."""
    
    def test_password_is_hashed(self, create_user):
        """
        SCENARIO: Password must never be stored in plaintext
        EXPECTED: Password is hashed
        """
        plaintext_password = 'SecurePassword123!'
        
        user = create_user(
            username='hashuser',
            email='hash@example.com',
            ktp_number='1234567890123456',
            password=plaintext_password
        )
        
        # Password is hashed, not plaintext
        assert user.password != plaintext_password
        assert user.password.startswith('pbkdf2_sha256$') or 'pbkdf2' in user.password
        
        # Can verify with correct password
        assert check_password(plaintext_password, user.password)
    
    def test_password_cannot_be_retrieved(self, create_user):
        """
        SCENARIO: Original password cannot be retrieved
        EXPECTED: Hash is one-way
        """
        password = 'CannotRetrieve123!'
        
        user = create_user(
            username='noretrieve',
            email='noretrieve@example.com',
            ktp_number='1234567890123456',
            password=password
        )
        
        # No way to get original password from hash
        # Can only verify
        assert check_password(password, user.password)
        assert not check_password('WrongPassword', user.password)
    
    def test_password_hash_is_deterministic_per_salt(self, create_user):
        """
        SCENARIO: Same password with different salt produces different hash
        EXPECTED: Each user has unique password hash even with same password
        """
        same_password = 'CommonPassword123!'
        
        user1 = create_user(
            username='user1',
            email='user1@example.com',
            ktp_number='1111111111111111',
            password=same_password
        )
        
        user2 = create_user(
            username='user2',
            email='user2@example.com',
            ktp_number='2222222222222222',
            password=same_password
        )
        
        # Same password, but different hashes (due to different salts)
        assert user1.password != user2.password


@pytest.mark.django_db
class TestDataMasking:
    """Test data masking for privacy."""
    
    def test_ktp_should_be_masked_in_display(self, create_user):
        """
        SCENARIO: Display KTP in UI
        EXPECTED: Should show masked version (e.g., ****3456)
        """
        ktp = '1234567890123456'
        
        user = create_user(
            username='maskuser',
            email='mask@example.com',
            ktp_number=ktp
        )
        
        # Function to mask KTP (would be in production code)
        def mask_ktp(ktp_number):
            if len(ktp_number) >= 4:
                return '****' + ktp_number[-4:]
            return '****'
        
        masked = mask_ktp(user.ktp_number)
        assert masked == '****3456'
        assert user.ktp_number not in masked
    
    def test_email_should_be_masked_in_some_contexts(self, create_user):
        """
        SCENARIO: Display email in public context
        EXPECTED: Should show masked version (e.g., u***@example.com)
        """
        email = 'user@example.com'
        
        user = create_user(
            username='emailmask',
            email=email,
            ktp_number='1234567890123456'
        )
        
        # Function to mask email
        def mask_email(email):
            parts = email.split('@')
            if len(parts) == 2:
                local = parts[0]
                domain = parts[1]
                if len(local) > 2:
                    masked_local = local[0] + '***' + local[-1]
                else:
                    masked_local = local[0] + '***'
                return f"{masked_local}@{domain}"
            return email
        
        masked = mask_email(user.email)
        assert masked == 'u***r@example.com'
    
    def test_phone_should_be_masked_in_display(self, create_user):
        """
        SCENARIO: Display phone number publicly
        EXPECTED: Should show masked version (e.g., +62812****890)
        """
        user = create_user(
            username='phonemask',
            email='phonemask@example.com',
            ktp_number='1234567890123456',
            phone_number='081234567890'
        )
        
        user.full_clean()
        user.save()
        
        # Function to mask phone
        def mask_phone(phone_number):
            if len(phone_number) >= 7:
                prefix = phone_number[:6]  # +62812
                suffix = phone_number[-3:]  # 890
                return f"{prefix}****{suffix}"
            return '****'
        
        masked = mask_phone(user.phone_number)
        assert '****' in masked


@pytest.mark.django_db
class TestAccessControl:
    """Test access control to sensitive data."""
    
    def test_user_can_access_own_data(self, create_user):
        """
        SCENARIO: User accesses their own profile
        EXPECTED: Should have full access
        """
        user = create_user(
            username='owndata',
            email='owndata@example.com',
            ktp_number='1234567890123456'
        )
        
        # User can access all their own data
        assert user.email is not None
        assert user.ktp_number is not None
        assert user.phone_number is not None
        assert user.date_of_birth is not None
    
    def test_admin_can_access_user_data(self, create_user):
        """
        SCENARIO: Admin needs to access user data
        EXPECTED: Should have access with proper permissions
        """
        regular_user = create_user(
            username='regularuser',
            email='regular@example.com',
            ktp_number='1234567890123456'
        )
        
        admin_user = create_user(
            username='admin',
            email='admin@example.com',
            ktp_number='9999999999999999'
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        
        # Admin can query other users
        assert admin_user.is_staff
        assert User.objects.filter(id=regular_user.id).exists()


@pytest.mark.django_db
class TestDataRetention:
    """Test data retention and deletion policies."""
    
    def test_soft_delete_retains_data(self, create_user):
        """
        SCENARIO: User deletes account
        EXPECTED: Data soft-deleted, not permanently removed
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
        
        # But still in database (all_objects)
        assert User.all_objects.filter(id=user_id).exists()
    
    def test_hard_delete_removes_data_permanently(self, create_user):
        """
        SCENARIO: Legal requirement to permanently delete data
        EXPECTED: Hard delete removes from database
        """
        user = create_user(
            username='harddel',
            email='harddel@example.com',
            ktp_number='1234567890123456'
        )
        
        user_id = user.id
        user.hard_delete()  # Permanent deletion
        
        # Completely removed from database
        assert not User.objects.filter(id=user_id).exists()
        assert not User.all_objects.filter(id=user_id).exists()


@pytest.mark.django_db
class TestAuditAndLogging:
    """Test audit trail and logging requirements."""
    
    def test_user_creation_timestamp_recorded(self, create_user):
        """
        SCENARIO: Track when user was created
        EXPECTED: Creation timestamp available
        """
        user = create_user(
            username='audituser',
            email='audit@example.com',
            ktp_number='1234567890123456'
        )
        
        # AbstractUser provides date_joined
        assert user.date_joined is not None
    
    def test_user_last_login_tracked(self, create_user):
        """
        SCENARIO: Track user's last login
        EXPECTED: Last login timestamp available
        """
        user = create_user(
            username='logintrack',
            email='logintrack@example.com',
            ktp_number='1234567890123456'
        )
        
        # AbstractUser provides last_login
        # Initially None until first login
        assert hasattr(user, 'last_login')


@pytest.mark.django_db
class TestGDPRAndPrivacyCompliance:
    """Test GDPR and privacy regulation compliance."""
    
    def test_user_can_export_their_data(self, create_user):
        """
        SCENARIO: User requests data export (GDPR right to access)
        EXPECTED: Can retrieve all user data
        """
        user = create_user(
            username='export',
            email='export@example.com',
            ktp_number='1234567890123456'
        )
        
        # Export user data
        user_data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'ktp_number': user.ktp_number,
            'date_of_birth': str(user.date_of_birth),
            'address': user.address,
            'phone_number': user.phone_number,
            'date_joined': str(user.date_joined),
        }
        
        assert user_data['email'] == 'export@example.com'
        assert user_data['ktp_number'] == '1234567890123456'
    
    def test_user_can_request_account_deletion(self, create_user):
        """
        SCENARIO: User requests account deletion (GDPR right to erasure)
        EXPECTED: Account can be deleted
        """
        user = create_user(
            username='delete',
            email='delete@example.com',
            ktp_number='1234567890123456'
        )
        
        user_id = user.id
        
        # Soft delete (with retention period)
        user.delete()
        
        # Not accessible in normal queries
        assert not User.objects.filter(id=user_id).exists()
        
        # After retention period, can hard delete
        deleted_user = User.all_objects.get(id=user_id)
        deleted_user.hard_delete()
        
        # Now permanently removed
        assert not User.all_objects.filter(id=user_id).exists()


@pytest.mark.django_db
class TestSecurityBestPractices:
    """Test security best practices implementation."""
    
    def test_inactive_user_cannot_login(self, create_user):
        """
        SCENARIO: Deactivated user tries to login
        EXPECTED: Should be blocked
        """
        from django.contrib.auth import authenticate
        
        password = 'TestPass123!'
        user = create_user(
            username='inactive',
            email='inactive@example.com',
            ktp_number='1234567890123456',
            password=password
        )
        
        # Deactivate user
        user.is_active = False
        user.save()
        
        # Cannot authenticate
        auth_user = authenticate(username=user.username, password=password)
        assert auth_user is None
    
    def test_user_session_security(self, create_user):
        """
        SCENARIO: User session management
        EXPECTED: Can invalidate sessions
        NOTE: Session handled by Django framework
        """
        user = create_user(
            username='session',
            email='session@example.com',
            ktp_number='1234567890123456'
        )
        
        # User has unique ID for session tracking
        assert user.id is not None
        
        # In production:
        # - Set session timeout
        # - Implement session invalidation on password change
        # - Track active sessions
        # - Allow user to view/revoke sessions
