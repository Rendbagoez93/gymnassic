from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from shared.base_models import SoftDelete


class User(AbstractUser, SoftDelete):
    # AbstractUser provides: username, first_name, last_name, email (base), password, groups, etc.
    
    # KTP (Indonesian ID Number) - 16 digits
    phone_regex = RegexValidator(
        regex=r'^(?:\+62|62|0)\d{9,13}$',
        message="Phone number must start with +62, 62, or 0 followed by 9-13 digits."
    )
    ktp_regex = RegexValidator(
        regex=r'^\d{16}$',
        message="KTP number must be exactly 16 digits."
    )
    
    ktp_number = models.CharField(
        max_length=16,
        validators=[ktp_regex],
        help_text="Indonesian ID number (KTP) - 16 digits",
        verbose_name="KTP Number"
    )
    
    # Date of Birth
    date_of_birth = models.DateField(
        help_text="User's date of birth",
        verbose_name="Date of Birth"
    )
    
    # Address
    address = models.TextField(
        help_text="User's complete address"
    )
    
    # Phone Number (flexible input, normalized storage)
    phone_number = models.CharField(
        max_length=17,
        validators=[phone_regex],
        help_text="Indonesian phone number (accepts +62, 62, or 0 prefix)"
    )
    
    class Meta:
        ordering = ['-date_joined']
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
        ]
        # Conditional unique constraints for soft-delete compatibility
        constraints = [
            models.UniqueConstraint(
                fields=['ktp_number'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_ktp_when_not_deleted'
            ),
            models.UniqueConstraint(
                fields=['email'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_email_when_not_deleted'
            ),
        ]
    
    def clean(self):
        """Normalize phone number to consistent +62 format."""
        super().clean()
        if self.phone_number:
            # Remove any whitespace
            phone = self.phone_number.strip().replace(' ', '').replace('-', '')
            # Normalize to +62 format
            if phone.startswith('0'):
                # Convert 08xx to +628xx
                phone = '+62' + phone[1:]
            elif phone.startswith('62'):
                # Convert 628xx to +628xx
                phone = '+' + phone
            # If already starts with +62, keep as is
            self.phone_number = phone
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.ktp_number})"
    
    @property
    def full_name(self):
        """Returns the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate and return the user's age based on date of birth."""
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year
        # Adjust if birthday hasn't occurred yet this year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
        return age
    
    def get_contact_info(self):
        """Returns a dictionary with the user's contact information."""
        return {
            'email': self.email,
            'phone': self.phone_number,
            'address': self.address
        }
