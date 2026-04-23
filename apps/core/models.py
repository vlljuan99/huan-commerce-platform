"""
Core models: base classes and shared utilities.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """
    Abstract model that automatically tracks creation and modification times.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    class Meta:
        abstract = True


class ActiveModel(models.Model):
    """
    Abstract model that tracks active/inactive state.
    Useful for soft deletes and logical deactivation.
    """
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel, ActiveModel):
    """
    Combined base model with timestamps and active state.
    Most models should inherit from this.
    """

    class Meta:
        abstract = True
