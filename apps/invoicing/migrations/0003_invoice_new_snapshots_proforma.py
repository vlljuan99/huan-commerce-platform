"""
Adds new snapshot fields to Invoice/InvoiceLineItem.
Creates ProformaInvoice and ProformaLineItem models.
"""

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("invoicing", "0002_invoice_fiscal_snapshots"),
        ("billing", "0001_initial"),
        ("customers", "0004_customer_code"),
    ]

    operations = [
        # ── Invoice: new snapshot + payment fields ────────────────────────────
        migrations.AddField(
            model_name="invoice",
            name="customer_code_snapshot",
            field=models.CharField(
                blank=True,
                max_length=20,
                verbose_name="Customer code (snapshot)",
                help_text="Cod.Cliente capturado en el momento de emisión",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="customer_phone_snapshot",
            field=models.CharField(
                blank=True,
                max_length=30,
                verbose_name="Customer phone (snapshot)",
                help_text="Teléfono del cliente capturado en el momento de emisión",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="billing_province_snapshot",
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name="Billing province (snapshot)",
                help_text="Provincia de facturación capturada en el momento de emisión",
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="payment_method",
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name="Payment method",
                help_text="e.g. GIRO A 30 DIAS, TRANSFERENCIA, CONTADO",
            ),
        ),
        # ── InvoiceLineItem: product code ─────────────────────────────────────
        migrations.AddField(
            model_name="invoicelineitem",
            name="product_code",
            field=models.CharField(
                blank=True,
                max_length=50,
                verbose_name="Product code",
                help_text="Código de artículo (COD.)",
            ),
        ),
        # ── ProformaInvoice ───────────────────────────────────────────────────
        migrations.CreateModel(
            name="ProformaInvoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("number", models.IntegerField(verbose_name="Proforma number")),
                ("proforma_number", models.CharField(max_length=20, unique=True, verbose_name="Full proforma number", help_text="e.g. 260001")),
                ("issued_at", models.DateTimeField(verbose_name="Issued at")),
                ("status", models.CharField(
                    choices=[
                        ("draft", "Borrador"),
                        ("sent", "Enviada"),
                        ("accepted", "Aceptada"),
                        ("rejected", "Rechazada"),
                        ("converted", "Convertida en factura"),
                        ("cancelled", "Cancelada"),
                    ],
                    default="draft",
                    max_length=20,
                    verbose_name="Status",
                )),
                ("subtotal", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, verbose_name="Subtotal (without tax)")),
                ("tax_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, verbose_name="Tax amount")),
                ("total", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, verbose_name="Total (with tax)")),
                ("billing_name_snapshot", models.CharField(blank=True, max_length=255, verbose_name="Billing name (snapshot)")),
                ("tax_id_snapshot", models.CharField(blank=True, max_length=50, verbose_name="Tax ID (snapshot)")),
                ("billing_address_snapshot", models.TextField(blank=True, verbose_name="Billing address (snapshot)")),
                ("customer_code_snapshot", models.CharField(blank=True, max_length=20, verbose_name="Customer code (snapshot)")),
                ("customer_phone_snapshot", models.CharField(blank=True, max_length=30, verbose_name="Customer phone (snapshot)")),
                ("billing_province_snapshot", models.CharField(blank=True, max_length=100, verbose_name="Billing province (snapshot)")),
                ("payment_method", models.CharField(blank=True, max_length=100, verbose_name="Payment method")),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                ("pdf_file", models.FileField(blank=True, null=True, upload_to="proformas/", verbose_name="PDF file")),
                ("customer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="proforma_invoices",
                    to="customers.customer",
                    verbose_name="Customer",
                )),
                ("converted_to_invoice", models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="from_proforma",
                    to="invoicing.invoice",
                    verbose_name="Converted to invoice",
                )),
            ],
            options={
                "verbose_name": "Proforma Invoice",
                "verbose_name_plural": "Proforma Invoices",
                "ordering": ["-issued_at"],
            },
        ),
        migrations.AddIndex(
            model_name="proformainvoice",
            index=models.Index(fields=["customer"], name="proforma_customer_idx"),
        ),
        migrations.AddIndex(
            model_name="proformainvoice",
            index=models.Index(fields=["status"], name="proforma_status_idx"),
        ),
        migrations.AddIndex(
            model_name="proformainvoice",
            index=models.Index(fields=["-issued_at"], name="proforma_issued_at_idx"),
        ),
        # ── ProformaLineItem ──────────────────────────────────────────────────
        migrations.CreateModel(
            name="ProformaLineItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("product_code", models.CharField(blank=True, max_length=50, verbose_name="Product code", help_text="Código de artículo (COD.)")),
                ("description", models.CharField(max_length=255, verbose_name="Description")),
                ("tono", models.CharField(blank=True, max_length=50, verbose_name="Tono", help_text="Color / tono del material")),
                ("quantity", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Quantity (UDS.)")),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Unit price (PVP, without tax)")),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Line total (without tax)")),
                ("tax_rate_pct", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5, verbose_name="Tax rate (%)")),
                ("tax_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, verbose_name="Tax amount (line)")),
                ("proforma", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="items",
                    to="invoicing.proformainvoice",
                    verbose_name="Proforma invoice",
                )),
                ("tax_rate", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    to="billing.taxrate",
                    verbose_name="Tax rate",
                )),
            ],
            options={
                "verbose_name": "Proforma Line Item",
                "verbose_name_plural": "Proforma Line Items",
            },
        ),
    ]
