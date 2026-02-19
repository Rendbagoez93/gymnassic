"""
Base models for the project.

This module provides abstract base models that can be inherited by app models
to add common functionality like timestamps, soft deletion, etc.
"""

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    class Meta:
        abstract = True
        ordering = ['-id']

    def __str__(self):
        return f"{self.__class__.__name__} #{self.id}"


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when the record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        help_text="Timestamp when the record was last updated"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Override save to ensure updated_at is set."""
        if not self.pk:
            # New instance
            if not self.created_at:
                self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

class SoftDeleteManager(models.Manager):
    """
    Manager that filters out soft-deleted objects by default.
    """
    def get_queryset(self):
        """Return only non-deleted objects."""
        return super().get_queryset().filter(deleted_at__isnull=True)

    def all_with_deleted(self):
        """Return all objects including soft-deleted ones."""
        return super().get_queryset()

    def deleted_only(self):
        """Return only soft-deleted objects."""
        return super().get_queryset().filter(deleted_at__isnull=False)

    def hard_delete(self):
        """Permanently delete all objects in the queryset."""
        return super().get_queryset().delete()


class SoftDelete(models.Model):
    # Field declarations
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp when the record was soft-deleted"
    )

    # Manager declarations
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Access to all objects including deleted

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False, deleted_by=None):
        """
        Soft delete the object by setting deleted_at timestamp.
        """
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)

        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self):
        """Permanently delete the object from the database."""
        super().delete()

    def restore(self):
        """Restore a soft-deleted object."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        """Check if the object is soft-deleted."""
        return self.deleted_at is not None

class SoftDeleteable(TimeStampedModel, SoftDelete, BaseModel):
    """
    Abstract model combining BaseModel, TimeStampedModel, and SoftDelete.
    """
    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Handle timestamps
        if not self.pk:
            if not self.created_at:
                self.created_at = timezone.now()
        self.updated_at = timezone.now()

        super().save(*args, **kwargs)
