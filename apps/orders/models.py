"""
Orders app: orders, order items, order states.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.core.models import BaseModel
from apps.customers.models import Customer
from apps.catalog.models import ProductVariant


class Order(BaseModel):
    """Main Order entity."""

    STATUS_CHOICES = [
        ("draft", _("Borrador")),
        ("pending", _("Pendiente")),
        ("confirmed", _("Confirmado")),
        ("processing", _("En proceso")),
        ("shipped", _("Enviado")),
        ("delivered", _("Entregado")),
        ("cancelled", _("Cancelado")),
    ]

    order_number = models.CharField(
        max_length=50, unique=True, verbose_name=_("Order number")
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("Customer"),
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name=_("Status")
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Subtotal"),
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Tax amount"),
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Shipping cost"),
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Total"),
    )

    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    # Address snapshots — frozen at order creation/confirmation
    shipping_address_snapshot = models.TextField(
        blank=True,
        verbose_name=_("Shipping address (snapshot)"),
        help_text=_("Address text captured when the order was placed"),
    )
    billing_address_snapshot = models.TextField(
        blank=True,
        verbose_name=_("Billing address (snapshot)"),
        help_text=_("Address text captured when the order was placed"),
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Confirmed at"),
        help_text=_("Set when order moves to confirmed status"),
    )

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Order {self.order_number}"


class OrderLineItem(BaseModel):
    """
    Individual line in an order.

    Snapshot fields (product_name, sku, unit_price, tax_rate_pct) are frozen at
    order creation so history stays accurate even when the catalog changes later.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("Order")
    )
    variant = models.ForeignKey(
        ProductVariant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Product variant"),
        help_text=_(
            "Live reference for convenience; source data is stored in snapshot fields below"
        ),
    )

    # ── Snapshot fields ────────────────────────────────────────────────
    product_name = models.CharField(
        max_length=255, verbose_name=_("Product name (snapshot)")
    )
    sku = models.CharField(max_length=100, blank=True, verbose_name=_("SKU (snapshot)"))

    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Quantity")
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Unit price (net)")
    )
    tax_rate_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Tax rate (%)"),
        help_text=_("e.g. 21.00 for 21% VAT"),
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Tax amount (line)"),
    )
    line_total = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Line total (net)")
    )

    class Meta:
        verbose_name = _("Order Line")
        verbose_name_plural = _("Order Lines")

    @property
    def line_total_with_tax(self):
        """Net line total plus tax."""
        return self.line_total + self.tax_amount

    def __str__(self):
        return f"{self.order} - {self.variant}"
