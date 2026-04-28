"""
Cart app: shopping cart items (transient, session-based).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.catalog.models import ProductVariant
from apps.services.models import Service


class Cart(models.Model):
    """
    Cart session (not persisted per se, can be session-based or user-based).
    """

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="cart",
        null=True,
        blank=True,
        verbose_name=_("User"),
    )
    session_key = models.CharField(
        max_length=40, unique=True, null=True, blank=True, verbose_name=_("Session key")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Shopping Cart")
        verbose_name_plural = _("Shopping Carts")

    def __str__(self):
        if self.user:
            return f"Cart of {self.user}"
        return f"Cart {self.session_key}"

    def get_total(self):
        """Calculate cart total."""
        return sum(item.get_total() for item in self.items.all())


class CartLineItem(models.Model):
    """Individual item in a cart."""

    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items", verbose_name=_("Cart")
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Product variant"),
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Service"),
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Cart Line Item")
        verbose_name_plural = _("Cart Line Items")
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                condition=models.Q(variant__isnull=False),
                name="unique_cart_variant",
            ),
            models.UniqueConstraint(
                fields=["cart", "service"],
                condition=models.Q(service__isnull=False),
                name="unique_cart_service",
            ),
        ]

    def __str__(self):
        if self.variant:
            return f"{self.variant} x {self.quantity}"
        if self.service:
            return f"{self.service} x {self.quantity}"
        return f"Item x {self.quantity}"

    @property
    def display_name(self):
        if self.variant:
            name = self.variant.product.name
            if self.variant.name:
                name += f" — {self.variant.name}"
            return name
        if self.service:
            return self.service.name
        return "—"

    @property
    def display_sku(self):
        if self.variant:
            return self.variant.sku
        if self.service:
            return self.service.sku or "—"
        return "—"

    @property
    def display_unit_price(self):
        if self.variant:
            return self.variant.price_no_tax
        if self.service:
            return self.service.price
        return Decimal("0")

    def get_total(self):
        return Decimal(self.quantity) * self.display_unit_price
