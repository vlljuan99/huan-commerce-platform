"""
Shipping app: shipping methods, costs, carriers.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class ShippingMethod(models.Model):
    """Available shipping methods."""

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Code"))
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Base cost"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    class Meta:
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")

    def __str__(self):
        return self.name


class Shipment(models.Model):
    """Shipment record for an order."""

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("shipped", _("Shipped")),
        ("in_transit", _("In transit")),
        ("delivered", _("Delivered")),
        ("failed", _("Failed")),
    ]

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="shipments",
        verbose_name=_("Order"),
    )

    method = models.ForeignKey(
        ShippingMethod, on_delete=models.PROTECT, verbose_name=_("Shipping method")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Status"),
    )

    tracking_number = models.CharField(
        max_length=255, blank=True, verbose_name=_("Tracking number")
    )

    cost = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Shipping cost")
    )

    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Shipment")
        verbose_name_plural = _("Shipments")
        ordering = ["-shipped_at"]

    def __str__(self):
        return f"Shipment {self.tracking_number} ({self.status})"
