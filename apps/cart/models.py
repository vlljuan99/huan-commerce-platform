"""
Cart app: shopping cart items (transient, session-based).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.catalog.models import ProductVariant


class Cart(models.Model):
    """
    Cart session (not persisted per se, can be session-based or user-based).
    """
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True,
        verbose_name=_('User')
    )
    session_key = models.CharField(
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_('Session key')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Shopping Cart')
        verbose_name_plural = _('Shopping Carts')

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
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Cart')
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        verbose_name=_('Product variant')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Quantity')
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Cart Line Item')
        verbose_name_plural = _('Cart Line Items')
        unique_together = ['cart', 'variant']

    def __str__(self):
        return f"{self.variant} x {self.quantity}"

    def get_total(self):
        """Get line total using current variant price."""
        return Decimal(self.quantity) * self.variant.price_no_tax
