#!/usr/bin/env python3
"""
Script to complete the Huan Commerce Platform structure.
Generates all remaining models, serializers, views, tests, factories, and configuration.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ============= ORDERS APP =============
orders_models = '''"""
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
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    ]
    
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Order number')
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('Customer')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Subtotal')
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Tax amount')
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Shipping cost')
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Total')
    )
    
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"


class OrderLineItem(BaseModel):
    """Individual line in an order."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Order')
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        verbose_name=_('Product variant')
    )
    
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Quantity')
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Unit price (without tax)')
    )
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Line total (without tax)')
    )
    
    class Meta:
        verbose_name = _('Order Line Item')
        verbose_name_plural = _('Order Line Items')

    def __str__(self):
        return f"{self.order} - {self.variant}"
'''

orders_file = BASE_DIR / 'apps' / 'orders' / 'models.py'
orders_file.write_text(orders_models)
print(f"✓ Created {orders_file}")

# ============= CART APP =============
cart_models = '''"""
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
'''

cart_file = BASE_DIR / 'apps' / 'cart' / 'models.py'
cart_file.write_text(cart_models)
print(f"✓ Created {cart_file}")

# ============= INVOICING APP =============
invoicing_models = '''"""
Invoicing app: invoices, states, line items, PDF rendering.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.core.models import BaseModel
from apps.customers.models import Customer


class InvoiceSeries(BaseModel):
    """Invoice series for numbering."""
    
    name = models.CharField(max_length=50, unique=True, verbose_name=_('Series name'))
    prefix = models.CharField(
        max_length=10,
        default='INV',
        verbose_name=_('Prefix'),
        help_text=_('e.g., INV, FACT')
    )
    next_number = models.IntegerField(
        default=1,
        verbose_name=_('Next number')
    )
    year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Year'),
        help_text=_('Reset number each year if set')
    )
    
    class Meta:
        verbose_name = _('Invoice Series')
        verbose_name_plural = _('Invoice Series')

    def __str__(self):
        return f"{self.name} ({self.prefix})"

    def get_next_number(self):
        """Get next invoice number and increment counter."""
        num = self.next_number
        self.next_number += 1
        self.save()
        return num


class Invoice(BaseModel):
    """Invoice entity."""
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('issued', _('Issued')),
        ('paid', _('Paid')),
        ('overdue', _('Overdue')),
        ('cancelled', _('Cancelled')),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name=_('Customer')
    )
    order = models.ForeignKey(
        'orders.Order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Related order'),
        help_text=_('1 invoice can come from 1 order, but 1 order can have N invoices')
    )
    
    series = models.ForeignKey(
        InvoiceSeries,
        on_delete=models.PROTECT,
        verbose_name=_('Invoice series')
    )
    number = models.IntegerField(verbose_name=_('Invoice number'))
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Full invoice number (formatted)'),
        help_text=_('e.g., INV-001')
    )
    
    issued_at = models.DateTimeField(verbose_name=_('Issued at'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Subtotal (without tax)')
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Tax amount')
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Total (with tax)')
    )
    
    pdf_file = models.FileField(
        upload_to='invoices/',
        null=True,
        blank=True,
        verbose_name=_('PDF file')
    )
    
    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['-issued_at']),
        ]
        unique_together = ['series', 'number']

    def __str__(self):
        return f"Invoice {self.invoice_number}"


class InvoiceLineItem(BaseModel):
    """Line item in an invoice."""
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Invoice')
    )
    
    description = models.CharField(max_length=255, verbose_name=_('Description'))
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Quantity')
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Unit price (without tax)')
    )
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Line total (without tax)')
    )
    tax_rate = models.ForeignKey(
        'billing.TaxRate',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Tax rate')
    )
    
    class Meta:
        verbose_name = _('Invoice Line Item')
        verbose_name_plural = _('Invoice Line Items')

    def __str__(self):
        return f"{self.invoice} - {self.description}"
'''

invoicing_file = BASE_DIR / 'apps' / 'invoicing' / 'models.py'
invoicing_file.write_text(invoicing_models)
print(f"✓ Created {invoicing_file}")

# ============= BILLING APP =============
billing_models = '''"""
Billing app: tax rates, fiscal rules, numerical series.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class TaxRate(models.Model):
    """Tax rate configuration."""
    
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Name'))
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Rate (%)'),
        help_text=_('e.g., 21.00 for 21%')
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('e.g., VAT_ES_STANDARD, VAT_ES_REDUCED')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    
    class Meta:
        verbose_name = _('Tax Rate')
        verbose_name_plural = _('Tax Rates')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    def calculate_tax(self, amount: Decimal) -> Decimal:
        """Calculate tax from amount."""
        return (amount * self.rate) / Decimal('100')
'''

billing_file = BASE_DIR / 'apps' / 'billing' / 'models.py'
billing_file.write_text(billing_models)
print(f"✓ Created {billing_file}")

# ============= PAYMENTS APP =============
payments_models = '''"""
Payments app: payment transactions, status tracking.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class PaymentTransaction(models.Model):
    """Payment transaction record."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('authorized', _('Authorized')),
        ('captured', _('Captured')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.PROTECT,
        related_name='payment_transactions',
        verbose_name=_('Order')
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Amount')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    
    provider = models.CharField(
        max_length=100,
        verbose_name=_('Payment provider'),
        help_text=_('e.g., redsys, stripe')
    )
    
    provider_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Provider transaction ID')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Payment Transaction')
        verbose_name_plural = _('Payment Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.order} - {self.status}"
'''

payments_file = BASE_DIR / 'apps' / 'payments' / 'models.py'
payments_file.write_text(payments_models)
print(f"✓ Created {payments_file}")

# ============= SHIPPING APP =============
shipping_models = '''"""
Shipping app: shipping methods, costs, carriers.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class ShippingMethod(models.Model):
    """Available shipping methods."""
    
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    code = models.CharField(max_length=50, unique=True, verbose_name=_('Code'))
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Base cost')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    
    class Meta:
        verbose_name = _('Shipping Method')
        verbose_name_plural = _('Shipping Methods')

    def __str__(self):
        return self.name


class Shipment(models.Model):
    """Shipment record for an order."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('shipped', _('Shipped')),
        ('in_transit', _('In transit')),
        ('delivered', _('Delivered')),
        ('failed', _('Failed')),
    ]
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='shipments',
        verbose_name=_('Order')
    )
    
    method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.PROTECT,
        verbose_name=_('Shipping method')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    
    tracking_number = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Tracking number')
    )
    
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Shipping cost')
    )
    
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Shipment')
        verbose_name_plural = _('Shipments')
        ordering = ['-shipped_at']

    def __str__(self):
        return f"Shipment {self.tracking_number} ({self.status})"
'''

shipping_file = BASE_DIR / 'apps' / 'shipping' / 'models.py'
shipping_file.write_text(shipping_models)
print(f"✓ Created {shipping_file}")

print("\n✓ All models generated successfully!")
