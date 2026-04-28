# Adds fiscal snapshot fields + due_date + notes to Invoice.
# Adds tax_rate_pct + tax_amount to InvoiceLineItem.

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("invoicing", "0001_initial"),
    ]

    operations = [
        # ── Invoice: fiscal snapshots ─────────────────────────────────────────
        migrations.AddField(
            model_name="invoice",
            name="billing_name_snapshot",
            field=models.CharField(
                max_length=255,
                blank=True,
                verbose_name="Billing name (snapshot)",
                help_text="Customer name as captured at invoice time",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="tax_id_snapshot",
            field=models.CharField(
                max_length=50,
                blank=True,
                verbose_name="Tax ID (snapshot)",
                help_text="Customer CIF/NIF as captured at invoice time",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="billing_address_snapshot",
            field=models.TextField(
                blank=True,
                verbose_name="Billing address (snapshot)",
                help_text="Billing address as captured at invoice time",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="due_date",
            field=models.DateField(
                null=True,
                blank=True,
                verbose_name="Due date",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="notes",
            field=models.TextField(
                blank=True,
                verbose_name="Notes",
            ),
        ),
        # ── InvoiceLineItem: tax snapshot ─────────────────────────────────────
        migrations.AddField(
            model_name="invoicelineitem",
            name="tax_rate_pct",
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=Decimal("0.00"),
                verbose_name="Tax rate (%)",
                help_text="Tax percentage at invoice time, e.g. 21.00",
            ),
        ),
        migrations.AddField(
            model_name="invoicelineitem",
            name="tax_amount",
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=Decimal("0.00"),
                verbose_name="Tax amount (line)",
            ),
        ),
    ]
