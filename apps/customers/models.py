"""
Customers app: customer data, addresses, segmentation.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.accounts.models import User


class Customer(BaseModel):
    """
    Customer profile linked to User account.
    Contains fiscal and segmentation data.
    """

    SEGMENT_CHOICES = [
        ("b2c", _("Particular")),
        ("b2b", _("Empresa")),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile",
        verbose_name=_("User"),
    )

    company_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Company name"),
        help_text=_("Nombre comercial. For B2B customers"),
    )

    fiscal_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Fiscal name"),
        help_text=_(
            "Nombre que aparece en facturas. B2C: nombre y apellidos. B2B: razón social."
        ),
    )

    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Tax ID"),
        help_text=_("CIF/NIF"),
    )

    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"))

    contact_email = models.EmailField(
        blank=True,
        verbose_name=_("Contact email"),
        help_text=_(
            "Email de contacto para facturas y comunicaciones. Puede diferir del email de acceso."
        ),
    )

    segment = models.CharField(
        max_length=10,
        choices=SEGMENT_CHOICES,
        default="b2c",
        verbose_name=_("Customer segment"),
    )

    notes = models.TextField(blank=True, verbose_name=_("Internal notes"))

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        ordering = ["-created_at"]

    def __str__(self):
        if self.company_name:
            return f"{self.company_name} ({self.user.get_full_name()})"
        return self.user.get_full_name() or self.user.email

    @property
    def display_name(self):
        """Nombre visible principal: comercial o nombre completo."""
        return self.company_name or self.user.get_full_name() or self.user.email

    @property
    def billing_name(self):
        """Nombre para facturas: fiscal_name > company_name > nombre completo."""
        return self.fiscal_name or self.company_name or self.user.get_full_name()

    @property
    def is_company(self):
        return self.segment == "b2b"

    def is_b2b(self):
        return self.segment == "b2b"

    def is_b2c(self):
        return self.segment == "b2c"


class CustomerAddress(BaseModel):
    """
    Address for a customer (shipping and billing).
    """

    ADDRESS_TYPE_CHOICES = [
        ("shipping", _("Shipping")),
        ("billing", _("Billing")),
        ("both", _("Shipping & Billing")),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("Customer"),
    )

    name = models.CharField(max_length=255, verbose_name=_("Address name"))
    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPE_CHOICES,
        default="both",
        verbose_name=_("Address type"),
    )

    # Address fields
    street_address = models.CharField(max_length=255, verbose_name=_("Street address"))
    city = models.CharField(max_length=100, verbose_name=_("City"))
    postal_code = models.CharField(max_length=20, verbose_name=_("Postal code"))
    region = models.CharField(max_length=100, blank=True, verbose_name=_("Region"))
    country = models.CharField(
        max_length=100, default="Spain", verbose_name=_("Country")
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Set as default"),
        help_text=_("Default address for new orders"),
    )

    class Meta:
        verbose_name = _("Customer Address")
        verbose_name_plural = _("Customer Addresses")
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.name} - {self.customer}"

    def save(self, *args, **kwargs):
        # Ensure only one default address per customer
        if self.is_default:
            CustomerAddress.objects.filter(
                customer=self.customer, address_type=self.address_type
            ).update(is_default=False)
        super().save(*args, **kwargs)

    def full_address(self):
        """Return full formatted address."""
        parts = [
            self.street_address,
            self.postal_code,
            self.city,
        ]
        if self.region:
            parts.append(self.region)
        parts.append(self.country)
        return ", ".join(parts)
