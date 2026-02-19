from django.core.validators import RegexValidator
from django.db import models

from shared.base_models import SoftDeleteable


class User(SoftDeleteable):
    # Name fields
    first_name = models.CharField(
        max_length=100,
        help_text="User's first name"
    )
    last_name = models.CharField(
        max_length=100,
        help_text="User's last name"
    )
    
    # KTP (Indonesian ID Number) - 16 digits
    phone_regex = RegexValidator(
        regex=r'^\+62\d{9,13}$',
        message="Phone number must be entered in the format: '+62812xxxxxxxx'. Indonesian numbers start with +62 followed by 9-13 digits."
    )
    ktp_regex = RegexValidator(
        regex=r'^\d{16}$',
        message="KTP number must be exactly 16 digits."
    )
    
    ktp_number = models.CharField(
        max_length=16,
        unique=True,
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
    
    # Phone Number
    phone_number = models.CharField(
        max_length=17,
        validators=[phone_regex],
        help_text="Indonesian phone number (format: +62812xxxxxxxx)"
    )
    
    # Email
    email = models.EmailField(
        unique=True,
        help_text="User's email address"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=['ktp_number']),
            models.Index(fields=['email']),
            models.Index(fields=['last_name', 'first_name']),
        ]
    
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
