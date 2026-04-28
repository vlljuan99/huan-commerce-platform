"""
Payments app: payment transactions, status tracking.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


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
