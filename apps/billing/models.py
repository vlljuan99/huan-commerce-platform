"""
Billing app: tax rates, fiscal rules, numerical series.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class TaxRate(models.Model):
    """Tax rate configuration."""

    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Rate (%)"),
        help_text=_("e.g., 21.00 for 21%"),
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("e.g., VAT_ES_STANDARD, VAT_ES_REDUCED"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    class Meta:
        verbose_name = _("Tax Rate")
        verbose_name_plural = _("Tax Rates")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    def calculate_tax(self, amount: Decimal) -> Decimal:
        """Calculate tax from amount."""
        return (amount * self.rate) / Decimal("100")
