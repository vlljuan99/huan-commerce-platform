# Adds address snapshots + confirmed_at to Order.
# Adds product snapshot fields + tax fields to OrderLineItem.
# Makes OrderLineItem.variant nullable/SET_NULL.

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        ("orders", "0001_initial"),
    ]

    operations = [
        # ── Order new fields ──────────────────────────────────────────────────
        migrations.AddField(
            model_name="order",
            name="shipping_address_snapshot",
            field=models.TextField(
                blank=True,
                verbose_name="Shipping address (snapshot)",
                help_text="Address text captured when the order was placed",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="billing_address_snapshot",
            field=models.TextField(
                blank=True,
                verbose_name="Billing address (snapshot)",
                help_text="Address text captured when the order was placed",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="confirmed_at",
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name="Confirmed at",
                help_text="Set when order moves to confirmed status",
            ),
        ),
        # ── OrderLineItem: make variant nullable ──────────────────────────────
        migrations.AlterField(
            model_name="orderlineitem",
            name="variant",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="catalog.productvariant",
                verbose_name="Product variant",
                help_text="Live reference for convenience; source data is stored in snapshot fields below",
            ),
        ),
        # ── OrderLineItem: snapshot + tax fields ──────────────────────────────
        migrations.AddField(
            model_name="orderlineitem",
            name="product_name",
            field=models.CharField(
                max_length=255,
                default="",
                verbose_name="Product name (snapshot)",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="orderlineitem",
            name="sku",
            field=models.CharField(
                max_length=100,
                blank=True,
                verbose_name="SKU (snapshot)",
            ),
        ),
        migrations.AddField(
            model_name="orderlineitem",
            name="tax_rate_pct",
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=Decimal("0.00"),
                verbose_name="Tax rate (%)",
                help_text="e.g. 21.00 for 21% VAT",
            ),
        ),
        migrations.AddField(
            model_name="orderlineitem",
            name="tax_amount",
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=Decimal("0.00"),
                verbose_name="Tax amount (line)",
            ),
        ),
        # ── OrderLineItem: rename verbose_names (no DB change) ────────────────
        migrations.AlterModelOptions(
            name="orderlineitem",
            options={
                "verbose_name": "Order Line",
                "verbose_name_plural": "Order Lines",
            },
        ),
    ]
