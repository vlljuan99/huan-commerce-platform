"""
Accounts models: custom User model with extensions.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.

    Allows future extensions like:
    - role-based access control
    - profile data
    - preferences
    """

    ROLE_CHOICES = [
        ("admin", _("Administrator")),
        ("commercial", _("Commercial")),
        ("customer", _("Customer")),
    ]

    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="customer", verbose_name=_("Role")
    )

    email = models.EmailField(unique=True, verbose_name=_("Email"))

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    def is_commercial(self):
        return self.role == "commercial"

    def is_customer(self):
        return self.role == "customer"
