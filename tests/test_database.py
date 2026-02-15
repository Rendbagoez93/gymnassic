"""
Test suite for database models and utilities.

Tests cover:
- BaseModel functionality
- TimeStampedModel automatic timestamps
- SoftDelete manager and soft deletion
- SoftDeleteable combined model
- Model lifecycle and edge cases
- Real-world database scenarios
"""

import pytest
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

from shared.base_models import (
    BaseModel,
    TimeStampedModel,
    SoftDelete,
    SoftDeleteManager,
    SoftDeleteable,
)


# ============================================================================
# TEST MODELS (Concrete implementations for testing)
# ============================================================================

class TestBaseModel(BaseModel):
    """Concrete model for testing BaseModel."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'tests'


class TestTimeStampedModel(TimeStampedModel):
    """Concrete model for testing TimeStampedModel."""
    title = models.CharField(max_length=200)
    
    class Meta:
        app_label = 'tests'


class TestSoftDeleteModel(SoftDelete, BaseModel):
    """Concrete model for testing SoftDelete."""
    description = models.TextField()
    
    class Meta:
        app_label = 'tests'


class TestSoftDeleteableModel(SoftDeleteable):
    """Concrete model for testing complete SoftDeleteable."""
    content = models.TextField()
    
    class Meta:
        app_label = 'tests'


# ============================================================================
# BASE MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestBaseModelFunctionality:
    """Test BaseModel abstract model."""

    def test_base_model_has_big_auto_field_id(self, db_fixture):
        """Test BaseModel uses BigAutoField for primary key."""
        obj = TestBaseModel.objects.create(name="Test Object")
        
        assert obj.id is not None
        assert isinstance(obj.id, int)
        assert obj.pk == obj.id

    def test_base_model_id_is_auto_increment(self, db_fixture):
        """Test ID auto-increments."""
        obj1 = TestBaseModel.objects.create(name="Object 1")
        obj2 = TestBaseModel.objects.create(name="Object 2")
        
        assert obj2.id > obj1.id

    def test_base_model_id_not_editable(self, db_fixture):
        """Test ID field is not editable."""
        model_field = TestBaseModel._meta.get_field('id')
        assert model_field.editable is False

    def test_base_model_string_representation(self, db_fixture):
        """Test __str__ method returns class name and ID."""
        obj = TestBaseModel.objects.create(name="Test")
        
        str_repr = str(obj)
        assert "TestBaseModel" in str_repr
        assert f"#{obj.id}" in str_repr

    def test_base_model_default_ordering(self, db_fixture):
        """Test default ordering is by -id (descending)."""
        obj1 = TestBaseModel.objects.create(name="First")
        obj2 = TestBaseModel.objects.create(name="Second")
        obj3 = TestBaseModel.objects.create(name="Third")
        
        all_objects = list(TestBaseModel.objects.all())
        
        # Should be ordered newest first (descending ID)
        assert all_objects[0].id == obj3.id
        assert all_objects[1].id == obj2.id
        assert all_objects[2].id == obj1.id


# ============================================================================
# TIMESTAMPED MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestTimeStampedModelFunctionality:
    """Test TimeStampedModel abstract model."""

    def test_created_at_auto_set_on_create(self, db_fixture):
        """Test created_at is automatically set when object is created."""
        before_create = timezone.now()
        obj = TestTimeStampedModel.objects.create(title="Test Title")
        after_create = timezone.now()
        
        assert obj.created_at is not None
        assert before_create <= obj.created_at <= after_create

    def test_updated_at_auto_set_on_create(self, db_fixture):
        """Test updated_at is automatically set when object is created."""
        before_create = timezone.now()
        obj = TestTimeStampedModel.objects.create(title="Test Title")
        after_create = timezone.now()
        
        assert obj.updated_at is not None
        assert before_create <= obj.updated_at <= after_create

    def test_updated_at_changes_on_save(self, db_fixture):
        """Test updated_at is updated when object is saved."""
        obj = TestTimeStampedModel.objects.create(title="Original Title")
        original_updated_at = obj.updated_at
        
        # Wait a tiny bit to ensure time difference
        import time
        time.sleep(0.01)
        
        obj.title = "Updated Title"
        obj.save()
        
        assert obj.updated_at > original_updated_at

    def test_created_at_does_not_change_on_update(self, db_fixture):
        """Test created_at remains the same after updates."""
        obj = TestTimeStampedModel.objects.create(title="Original")
        original_created_at = obj.created_at
        
        obj.title = "Updated"
        obj.save()
        
        obj.refresh_from_db()
        assert obj.created_at == original_created_at

    def test_timestamped_model_default_ordering(self, db_fixture):
        """Test default ordering is by -created_at (newest first)."""
        obj1 = TestTimeStampedModel.objects.create(title="First")
        obj2 = TestTimeStampedModel.objects.create(title="Second")
        obj3 = TestTimeStampedModel.objects.create(title="Third")
        
        all_objects = list(TestTimeStampedModel.objects.all())
        
        # Should be ordered newest first
        assert all_objects[0].id == obj3.id
        assert all_objects[1].id == obj2.id
        assert all_objects[2].id == obj1.id

    def test_created_at_has_db_index(self, db_fixture):
        """Test created_at field has database index."""
        field = TestTimeStampedModel._meta.get_field('created_at')
        assert field.db_index is True

    def test_updated_at_has_db_index(self, db_fixture):
        """Test updated_at field has database index."""
        field = TestTimeStampedModel._meta.get_field('updated_at')
        assert field.db_index is True


# ============================================================================
# SOFT DELETE MANAGER TESTS
# ============================================================================

@pytest.mark.django_db
class TestSoftDeleteManagerFunctionality:
    """Test SoftDeleteManager."""

    def test_manager_filters_deleted_objects_by_default(self, db_fixture):
        """Test default manager excludes soft-deleted objects."""
        obj1 = TestSoftDeleteModel.objects.create(description="Active")
        obj2 = TestSoftDeleteModel.objects.create(description="To be deleted")
        
        obj2.delete()  # Soft delete
        
        active_objects = TestSoftDeleteModel.objects.all()
        assert active_objects.count() == 1
        assert obj1 in active_objects
        assert obj2 not in active_objects

    def test_all_with_deleted_returns_all_objects(self, db_fixture):
        """Test all_with_deleted() returns both active and deleted."""
        obj1 = TestSoftDeleteModel.objects.create(description="Active")
        obj2 = TestSoftDeleteModel.objects.create(description="Deleted")
        
        obj2.delete()
        
        all_objects = TestSoftDeleteModel.objects.all_with_deleted()
        assert all_objects.count() == 2
        assert obj1 in all_objects
        assert obj2 in all_objects

    def test_deleted_only_returns_soft_deleted_objects(self, db_fixture):
        """Test deleted_only() returns only soft-deleted objects."""
        obj1 = TestSoftDeleteModel.objects.create(description="Active")
        obj2 = TestSoftDeleteModel.objects.create(description="Deleted 1")
        obj3 = TestSoftDeleteModel.objects.create(description="Deleted 2")
        
        obj2.delete()
        obj3.delete()
        
        deleted_objects = TestSoftDeleteModel.objects.deleted_only()
        assert deleted_objects.count() == 2
        assert obj1 not in deleted_objects
        assert obj2 in deleted_objects
        assert obj3 in deleted_objects

    def test_all_objects_manager_returns_everything(self, db_fixture):
        """Test all_objects manager returns all records including deleted."""
        obj1 = TestSoftDeleteModel.objects.create(description="Active")
        obj2 = TestSoftDeleteModel.objects.create(description="Deleted")
        
        obj2.delete()
        
        all_records = TestSoftDeleteModel.all_objects.all()
        assert all_records.count() == 2


# ============================================================================
# SOFT DELETE MODEL TESTS
# ============================================================================

@pytest.mark.django_db
class TestSoftDeleteFunctionality:
    """Test SoftDelete model functionality."""

    def test_soft_delete_sets_deleted_at_timestamp(self, db_fixture):
        """Test soft delete sets deleted_at timestamp."""
        obj = TestSoftDeleteModel.objects.create(description="Test")
        
        assert obj.deleted_at is None
        
        before_delete = timezone.now()
        obj.delete()
        after_delete = timezone.now()
        
        obj.refresh_from_db()
        assert obj.deleted_at is not None
        assert before_delete <= obj.deleted_at <= after_delete

    def test_soft_delete_does_not_remove_from_database(self, db_fixture):
        """Test soft delete keeps record in database."""
        obj = TestSoftDeleteModel.objects.create(description="Test")
        obj_id = obj.id
        
        obj.delete()
        
        # Should still exist in database
        all_records = TestSoftDeleteModel.all_objects.filter(id=obj_id)
        assert all_records.exists()

    def test_hard_delete_removes_from_database(self, db_fixture):
        """Test hard delete permanently removes record."""
        obj = TestSoftDeleteModel.objects.create(description="Test")
        obj_id = obj.id
        
        obj.delete(hard=True)
        
        # Should not exist in database
        all_records = TestSoftDeleteModel.all_objects.filter(id=obj_id)
        assert not all_records.exists()

    def test_hard_delete_method_removes_from_database(self, db_fixture):
        """Test hard_delete() method permanently removes record."""
        obj = TestSoftDeleteModel.objects.create(description="Test")
        obj_id = obj.id
        
        obj.hard_delete()
        
        all_records = TestSoftDeleteModel.all_objects.filter(id=obj_id)
        assert not all_records.exists()

    def test_restore_undeletes_soft_deleted_object(self, db_fixture):
        """Test restore() sets deleted_at back to None."""
        obj = TestSoftDeleteModel.objects.create(description="Test")
        
        obj.delete()  # Soft delete
        assert obj.deleted_at is not None
        
        obj.restore()
        assert obj.deleted_at is None
        
        # Should appear in default queryset again
        active_objects = TestSoftDeleteModel.objects.all()
        assert obj in active_objects

    def test_is_deleted_property(self, db_fixture):
        """Test is_deleted property correctly identifies deletion status."""
        obj = TestSoftDeleteModel.objects.create(description="Test")
        
        assert obj.is_deleted is False
        
        obj.delete()
        assert obj.is_deleted is True
        
        obj.restore()
        assert obj.is_deleted is False

    def test_deleted_at_has_db_index(self, db_fixture):
        """Test deleted_at field has database index for performance."""
        field = TestSoftDeleteModel._meta.get_field('deleted_at')
        assert field.db_index is True


# ============================================================================
# SOFT DELETEABLE MODEL TESTS (Combined)
# ============================================================================

@pytest.mark.django_db
class TestSoftDeleteableModelFunctionality:
    """Test SoftDeleteable combined model."""

    def test_soft_deleteable_has_all_features(self, db_fixture):
        """Test SoftDeleteable combines all base model features."""
        obj = TestSoftDeleteableModel.objects.create(content="Test Content")
        
        # Has ID from BaseModel
        assert obj.id is not None
        
        # Has timestamps from TimeStampedModel
        assert obj.created_at is not None
        assert obj.updated_at is not None
        
        # Has soft delete capability
        assert obj.deleted_at is None
        assert obj.is_deleted is False

    def test_soft_deleteable_timestamps_update_correctly(self, db_fixture):
        """Test timestamp handling in SoftDeleteable."""
        obj = TestSoftDeleteableModel.objects.create(content="Original")
        original_created = obj.created_at
        original_updated = obj.updated_at
        
        import time
        time.sleep(0.01)
        
        obj.content = "Updated"
        obj.save()
        
        assert obj.created_at == original_created
        assert obj.updated_at > original_updated

    def test_soft_deleteable_soft_delete_workflow(self, db_fixture):
        """Test complete soft delete workflow."""
        obj = TestSoftDeleteableModel.objects.create(content="Test")
        
        # Soft delete
        obj.delete()
        assert obj.is_deleted is True
        
        # Not in default queryset
        assert TestSoftDeleteableModel.objects.count() == 0
        
        # Still in all_objects
        assert TestSoftDeleteableModel.all_objects.count() == 1
        
        # Restore
        obj.restore()
        assert obj.is_deleted is False
        assert TestSoftDeleteableModel.objects.count() == 1

    def test_soft_deleteable_ordering(self, db_fixture):
        """Test SoftDeleteable uses created_at for ordering."""
        obj1 = TestSoftDeleteableModel.objects.create(content="First")
        obj2 = TestSoftDeleteableModel.objects.create(content="Second")
        obj3 = TestSoftDeleteableModel.objects.create(content="Third")
        
        all_objects = list(TestSoftDeleteableModel.objects.all())
        
        # Should be ordered newest first
        assert all_objects[0].id == obj3.id
        assert all_objects[1].id == obj2.id
        assert all_objects[2].id == obj1.id


# ============================================================================
# REAL-WORLD SCENARIO TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.django_db
class TestRealWorldDatabaseScenarios:
    """Test real-world database usage scenarios."""

    def test_user_account_soft_deletion_scenario(self, db_fixture):
        """
        Scenario: User deletes their account but we keep the data for 30 days.
        """
        # Create user account
        user = TestSoftDeleteableModel.objects.create(content="user@example.com")
        
        # User requests account deletion
        user.delete()
        
        # User should not appear in active queries
        active_users = TestSoftDeleteableModel.objects.all()
        assert user not in active_users
        
        # Admin can still see deleted accounts
        all_users = TestSoftDeleteableModel.all_objects.all()
        assert user in all_users
        
        # User changes mind and restores account within 30 days
        user.restore()
        assert user in TestSoftDeleteableModel.objects.all()

    def test_bulk_soft_delete_and_restore(self, db_fixture):
        """
        Scenario: Bulk operations on multiple records.
        """
        # Create multiple records
        objects = [
            TestSoftDeleteableModel.objects.create(content=f"Item {i}")
            for i in range(5)
        ]
        
        # Soft delete first 3
        for obj in objects[:3]:
            obj.delete()
        
        # Check counts
        assert TestSoftDeleteableModel.objects.count() == 2
        assert TestSoftDeleteableModel.objects.deleted_only().count() == 3
        
        # Restore all deleted
        for obj in TestSoftDeleteableModel.objects.deleted_only():
            obj.restore()
        
        assert TestSoftDeleteableModel.objects.count() == 5

    def test_audit_trail_with_timestamps(self, db_fixture):
        """
        Scenario: Track when records were created, updated, and deleted.
        """
        obj = TestSoftDeleteableModel.objects.create(content="Important Document")
        
        created_time = obj.created_at
        
        # Update document
        import time
        time.sleep(0.01)
        obj.content = "Important Document (Revised)"
        obj.save()
        
        updated_time = obj.updated_at
        assert updated_time > created_time
        
        # Delete document
        time.sleep(0.01)
        obj.delete()
        
        deleted_time = obj.deleted_at
        assert deleted_time is not None
        assert deleted_time > updated_time
        
        # We now have complete audit trail
        assert obj.created_at < obj.updated_at < obj.deleted_at

    def test_filtering_by_date_range(self, db_fixture):
        """
        Scenario: Find records created in a specific time period.
        """
        # Create records at different times
        now = timezone.now()
        
        obj1 = TestSoftDeleteableModel.objects.create(content="Old record")
        # Manually set created_at to simulate old record
        TestSoftDeleteableModel.all_objects.filter(id=obj1.id).update(
            created_at=now - timedelta(days=10)
        )
        
        obj2 = TestSoftDeleteableModel.objects.create(content="Recent record")
        
        # Find records created in last 7 days
        recent_cutoff = now - timedelta(days=7)
        recent_records = TestSoftDeleteableModel.objects.filter(
            created_at__gte=recent_cutoff
        )
        
        assert obj2 in recent_records
        assert obj1 not in recent_records

    def test_permanent_deletion_after_retention_period(self, db_fixture):
        """
        Scenario: Permanently delete records deleted more than 30 days ago.
        """
        # Create and soft delete multiple records
        old_obj = TestSoftDeleteableModel.objects.create(content="Old deleted record")
        recent_obj = TestSoftDeleteableModel.objects.create(content="Recent deleted record")
        
        old_obj.delete()
        recent_obj.delete()
        
        # Simulate old deletion (>30 days ago)
        old_deletion_time = timezone.now() - timedelta(days=31)
        TestSoftDeleteableModel.all_objects.filter(id=old_obj.id).update(
            deleted_at=old_deletion_time
        )
        
        # Find records deleted more than 30 days ago
        retention_cutoff = timezone.now() - timedelta(days=30)
        old_deleted = TestSoftDeleteableModel.all_objects.filter(
            deleted_at__lt=retention_cutoff
        )
        
        # Permanently delete old records
        for obj in old_deleted:
            obj.hard_delete()
        
        # Old record should be gone
        assert not TestSoftDeleteableModel.all_objects.filter(id=old_obj.id).exists()
        
        # Recent record should still exist
        assert TestSoftDeleteableModel.all_objects.filter(id=recent_obj.id).exists()

    def test_cascade_soft_delete_simulation(self, db_fixture):
        """
        Scenario: When deleting a parent, mark related children as deleted too.
        (This is a simplified simulation without actual foreign keys)
        """
        parent = TestSoftDeleteableModel.objects.create(content="Parent Record")
        child1 = TestSoftDeleteableModel.objects.create(content=f"Child of {parent.id}")
        child2 = TestSoftDeleteableModel.objects.create(content=f"Child of {parent.id}")
        
        # Soft delete parent
        parent.delete()
        
        # In real scenario, you'd also soft delete children
        # Simulating that here
        child1.delete()
        child2.delete()
        
        # All should be soft deleted
        assert parent.is_deleted
        assert child1.is_deleted
        assert child2.is_deleted
        
        # None should appear in default queries
        assert TestSoftDeleteableModel.objects.count() == 0
        
        # All should still exist in database
        assert TestSoftDeleteableModel.all_objects.count() == 3
