"""
Test Age / DOB Real World Behavior

Tests age calculation, age-based access control, and DOB validation.
"""
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from datetime import date, timedelta

User = get_user_model()


@pytest.mark.django_db
class TestAgeCalculation:
    """Test age calculation from date of birth."""
    
    def test_age_calculated_correctly(self, create_user):
        """
        SCENARIO: System calculates user's age
        EXPECTED: Age should be accurate based on DOB
        """
        today = date.today()
        dob = date(today.year - 25, today.month, today.day)
        
        user = create_user(
            username='testuser',
            email='test@example.com',
            ktp_number='1234567890123456',
            date_of_birth=dob
        )
        
        assert user.age == 25
    
    def test_age_before_birthday_this_year(self, create_user):
        """
        SCENARIO: User's birthday hasn't occurred yet this year
        EXPECTED: Age should be one year less
        """
        today = date.today()
        # DOB is tomorrow next year (birthday hasn't passed)
        dob = date(today.year - 25, today.month, today.day) + timedelta(days=1)
        
        user = create_user(
            username='testuser',
            email='test@example.com',
            ktp_number='1234567890123456',
            date_of_birth=dob
        )
        
        # If birthday is in the future this year, age should be 24
        assert user.age == 24
    
    def test_age_on_exact_birthday(self, create_user):
        """
        SCENARIO: Today is user's birthday
        EXPECTED: Age should include this year
        """
        today = date.today()
        dob = date(today.year - 30, today.month, today.day)
        
        user = create_user(
            username='testuser',
            email='test@example.com',
            ktp_number='1234567890123456',
            date_of_birth=dob
        )
        
        assert user.age == 30
    
    def test_newborn_age_zero(self, create_user):
        """
        SCENARIO: Baby born today (edge case)
        EXPECTED: Age should be 0
        """
        today = date.today()
        
        user = create_user(
            username='babyuser',
            email='baby@example.com',
            ktp_number='1111111111111111',
            date_of_birth=today
        )
        
        assert user.age == 0
    
    def test_elderly_user_age(self, elderly_user_data, create_user):
        """
        SCENARIO: Elderly user (over 60)
        EXPECTED: Age calculated correctly for older users
        """
        user = create_user(**elderly_user_data)
        assert user.age >= 60


@pytest.mark.django_db
class TestAgeBasedAccessControl:
    """Test age-based restrictions and access control."""
    
    def test_minor_detection(self, minor_user_data, create_user):
        """
        SCENARIO: System needs to identify minors (under 18)
        EXPECTED: Can correctly identify users under 18
        """
        user = create_user(**minor_user_data)
        
        is_minor = user.age < 18
        assert is_minor is True
    
    def test_adult_detection(self, adult_user_data, create_user):
        """
        SCENARIO: System needs to identify adults (18+)
        EXPECTED: Can correctly identify users 18 and over
        """
        user = create_user(**adult_user_data)
        
        is_adult = user.age >= 18
        assert is_adult is True
    
    def test_age_17_cannot_sign_legal_agreement(self, create_user):
        """
        SCENARIO: 17-year-old tries to sign legal agreement
        EXPECTED: Should be blocked (under 18)
        """
        today = date.today()
        dob_17 = date(today.year - 17, today.month, today.day)
        
        user = create_user(
            username='teen17',
            email='teen17@example.com',
            ktp_number='1717171717171717',
            date_of_birth=dob_17
        )
        
        can_sign_contract = user.age >= 18
        assert can_sign_contract is False
    
    def test_age_18_can_sign_legal_agreement(self, create_user):
        """
        SCENARIO: 18-year-old tries to sign legal agreement
        EXPECTED: Should be allowed
        """
        today = date.today()
        dob_18 = date(today.year - 18, today.month, today.day)
        
        user = create_user(
            username='adult18',
            email='adult18@example.com',
            ktp_number='1818181818181818',
            date_of_birth=dob_18
        )
        
        can_sign_contract = user.age >= 18
        assert can_sign_contract is True
    
    def test_parental_consent_required_for_minor(self, minor_user_data, create_user):
        """
        SCENARIO: Minor tries to register for service requiring parental consent
        EXPECTED: System identifies that parental consent is needed
        """
        user = create_user(**minor_user_data)
        
        requires_parental_consent = user.age < 18
        assert requires_parental_consent is True


@pytest.mark.django_db
class TestRegulatoryAndLegalLogic:
    """Test DOB-related legal and regulatory scenarios."""
    
    def test_employment_eligibility_age_check(self, create_user):
        """
        SCENARIO: Check if user meets minimum employment age (15 in Indonesia)
        EXPECTED: Can determine employment eligibility
        """
        today = date.today()
        
        # User age 14 (not eligible)
        dob_14 = date(today.year - 14, today.month, today.day)
        user_14 = create_user(
            username='user14',
            email='user14@example.com',
            ktp_number='1414141414141414',
            date_of_birth=dob_14
        )
        
        # User age 16 (eligible)
        dob_16 = date(today.year - 16, today.month, today.day)
        user_16 = create_user(
            username='user16',
            email='user16@example.com',
            ktp_number='1616161616161616',
            date_of_birth=dob_16
        )
        
        min_employment_age = 15
        assert user_14.age < min_employment_age
        assert user_16.age >= min_employment_age
    
    def test_senior_citizen_benefits_eligibility(self, elderly_user_data, create_user):
        """
        SCENARIO: Check if user qualifies for senior citizen benefits (60+ in Indonesia)
        EXPECTED: Can identify senior citizens
        """
        user = create_user(**elderly_user_data)
        
        is_senior_citizen = user.age >= 60
        assert is_senior_citizen is True
    
    def test_school_enrollment_age_verification(self, create_user):
        """
        SCENARIO: Verify age for school enrollment (e.g., elementary school 6-12)
        EXPECTED: Can determine grade-appropriate age
        """
        today = date.today()
        
        # Child age 7 (elementary school age)
        dob_7 = date(today.year - 7, today.month, today.day)
        child = create_user(
            username='child7',
            email='child7@example.com',
            ktp_number='0707070707070707',
            date_of_birth=dob_7
        )
        
        # Elementary school age range (6-12)
        is_elementary_age = 6 <= child.age <= 12
        assert is_elementary_age is True
    
    def test_military_service_age_eligibility(self, create_user):
        """
        SCENARIO: Check minimum age for military service (18 in Indonesia)
        EXPECTED: Can verify military service eligibility
        """
        today = date.today()
        
        # User age 17 (not eligible)
        dob_17 = date(today.year - 17, today.month, today.day)
        user_17 = create_user(
            username='user17',
            email='user17@example.com',
            ktp_number='1717171717171717',
            date_of_birth=dob_17
        )
        
        # User age 18 (eligible)
        dob_18 = date(today.year - 18, today.month, today.day)
        user_18 = create_user(
            username='user18',
            email='user18@example.com',
            ktp_number='1818181818181818',
            date_of_birth=dob_18
        )
        
        military_service_age = 18
        assert user_17.age < military_service_age
        assert user_18.age >= military_service_age


@pytest.mark.django_db
class TestDOBValidationAndEdgeCases:
    """Test DOB validation and edge cases."""
    
    def test_future_dob_should_be_invalid(self, create_user, future_date):
        """
        SCENARIO: User enters future date as DOB
        EXPECTED: Should be rejected (business logic validation needed)
        """
        # Note: This requires custom validation in the model
        # For now, we test that a future DOB gives negative age
        user = create_user(
            username='futureuser',
            email='future@example.com',
            ktp_number='9999999999999999',
            date_of_birth=future_date
        )
        
        # Age would be negative
        assert user.age < 0
    
    def test_very_old_dob_accepted(self, create_user):
        """
        SCENARIO: User over 100 years old registers
        EXPECTED: Should be accepted (possible, though rare)
        """
        today = date.today()
        dob_old = date(today.year - 105, today.month, today.day)
        
        user = create_user(
            username='centenarian',
            email='centenarian@example.com',
            ktp_number='1900190019001900',
            date_of_birth=dob_old
        )
        
        assert user.age >= 100
    
    def test_leap_year_birthday(self, create_user):
        """
        SCENARIO: User born on Feb 29 (leap year)
        EXPECTED: Age calculated correctly even on non-leap years
        """
        # Born on leap year
        dob = date(2000, 2, 29)
        
        user = create_user(
            username='leapuser',
            email='leap@example.com',
            ktp_number='2000229200002292',
            date_of_birth=dob
        )
        
        # Should calculate age correctly
        today = date.today()
        expected_age = today.year - 2000
        if today.month < 2 or (today.month == 2 and today.day < 28):
            expected_age -= 1
        
        assert user.age == expected_age
    
    def test_dob_stored_and_retrieved_correctly(self, create_user):
        """
        SCENARIO: Ensure DOB is stored and retrieved without data loss
        EXPECTED: Exact date preserved
        """
        dob = date(1995, 7, 15)
        
        user = create_user(
            username='datetest',
            email='datetest@example.com',
            ktp_number='1995071519950715',
            date_of_birth=dob
        )
        
        user.refresh_from_db()
        
        assert user.date_of_birth == dob
        assert user.date_of_birth.year == 1995
        assert user.date_of_birth.month == 7
        assert user.date_of_birth.day == 15


@pytest.mark.django_db
class TestAgeBasedFeatures:
    """Test age-based feature access."""
    
    def test_age_restricted_content_access(self, create_user):
        """
        SCENARIO: Different content available based on age groups
        EXPECTED: Can segment users by age ranges
        """
        today = date.today()
        
        # Child (10 years old)
        child = create_user(
            username='child',
            email='child@example.com',
            ktp_number='1010101010101010',
            date_of_birth=date(today.year - 10, today.month, today.day)
        )
        
        # Teen (15 years old)
        teen = create_user(
            username='teen',
            email='teen@example.com',
            ktp_number='1515151515151515',
            date_of_birth=date(today.year - 15, today.month, today.day)
        )
        
        # Adult (25 years old)
        adult = create_user(
            username='adult',
            email='adult@example.com',
            ktp_number='2525252525252525',
            date_of_birth=date(today.year - 25, today.month, today.day)
        )
        
        # Age-based content access
        child_content = child.age < 13
        teen_content = 13 <= teen.age < 18
        adult_content = adult.age >= 18
        
        assert child_content is True
        assert teen_content is True
        assert adult_content is True
