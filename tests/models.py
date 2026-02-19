"""
Test models for database testing.

These concrete model implementations are used to test the abstract base models
defined in shared.base_models.
"""

from django.db import models

from shared.base_models import (
    BaseModel,
    SoftDelete,
    SoftDeleteable,
    TimeStampedModel,
)


class ConcreteBaseModel(BaseModel):
    """Concrete model for testing BaseModel."""
    name = models.CharField(max_length=100)
    
    class Meta(BaseModel.Meta):
        app_label = 'tests'


class ConcreteTimeStampedModel(TimeStampedModel):
    """Concrete model for testing TimeStampedModel."""
    title = models.CharField(max_length=200)
    
    class Meta(TimeStampedModel.Meta):
        app_label = 'tests'


class ConcreteSoftDeleteModel(SoftDelete, BaseModel):
    """Concrete model for testing SoftDelete."""
    description = models.TextField()
    
    class Meta(BaseModel.Meta):
        app_label = 'tests'


class ConcreteSoftDeleteableModel(SoftDeleteable):
    """Concrete model for testing complete SoftDeleteable."""
    content = models.TextField()
    
    class Meta(SoftDeleteable.Meta):
        app_label = 'tests'
