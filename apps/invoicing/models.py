"""
Invoicing app: invoices, states, line items, proforma invoices, PDF rendering.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.core.models import BaseModel
from apps.customers.models import Customer


class InvoiceSeries(BaseModel):
    """Invoice series for numbering."""

    name = models.CharField(max_length=50, unique=True, verbose_name=_("Series name"))
    prefix = models.CharField(
        max_length=10,
        default="INV",
        verbose_name=_("Prefix"),
        help_text=_("e.g., INV, FACT"),
    )
    next_number = models.IntegerField(default=1, verbose_name=_("Next number"))
    year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Year"),
        help_text=_("Reset number each year if set"),
    )

    class Meta:
        verbose_name = _("Invoice Series")
        verbose_name_plural = _("Invoice Series")

    def __str__(self):
        return f"{self.name} ({self.prefix})"

    def get_next_number(self):
        """Get next invoice number and increment counter atomically."""
        from django.db import transaction

        with transaction.atomic():
            series = InvoiceSeries.objects.select_for_update().get(pk=self.pk)
            num = series.next_number
            series.next_number += 1
            series.save(update_fields=["next_number"])
        self.refresh_from_db()
        return num


class Invoice(BaseModel):
    """Invoice entity."""

    STATUS_CHOICES = [
        ("draft", _("Borrador")),
        ("issued", _("Emitida")),
        ("paid", _("Pagada")),
        ("overdue", _("Vencida")),
        ("cancelled", _("Cancelada")),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="invoices",
        verbose_name=_("Customer"),
    )
    order = models.ForeignKey(
        "orders.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Related order"),
        help_text=_("1 invoice can come from 1 order, but 1 order can have N invoices"),
    )

    series = models.ForeignKey(
        InvoiceSeries, on_delete=models.PROTECT, verbose_name=_("Invoice series")
    )
    number = models.IntegerField(verbose_name=_("Invoice number"))
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Full invoice number (formatted)"),
        help_text=_("e.g., INV-001"),
    )

    issued_at = models.DateTimeField(verbose_name=_("Issued at"))
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name=_("Status")
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Subtotal (without tax)"),
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Tax amount"),
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Total (with tax)"),
    )

    # Fiscal snapshot — frozen at invoice issuance
    billing_name_snapshot = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Billing name (snapshot)"),
        help_text=_("Customer name as captured at invoice time"),
    )
    tax_id_snapshot = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Tax ID (snapshot)"),
        help_text=_("Customer CIF/NIF as captured at invoice time"),
    )
    billing_address_snapshot = models.TextField(
        blank=True,
        verbose_name=_("Billing address (snapshot)"),
        help_text=_("Billing address as captured at invoice time"),
    )
    customer_code_snapshot = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Customer code (snapshot)"),
        help_text=_("Cod.Cliente capturado en el momento de emisión"),
    )
    customer_phone_snapshot = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_("Customer phone (snapshot)"),
        help_text=_("Teléfono del cliente capturado en el momento de emisión"),
    )
    billing_province_snapshot = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Billing province (snapshot)"),
        help_text=_("Provincia de facturación capturada en el momento de emisión"),
    )

    payment_method = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Payment method"),
        help_text=_("e.g. GIRO A 30 DIAS, TRANSFERENCIA, CONTADO"),
    )
    due_date = models.DateField(null=True, blank=True, verbose_name=_("Due date"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    pdf_file = models.FileField(
        upload_to="invoices/", null=True, blank=True, verbose_name=_("PDF file")
    )

    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-issued_at"]),
        ]
        unique_together = ["series", "number"]

    def __str__(self):
        return f"Invoice {self.invoice_number}"


class InvoiceLineItem(BaseModel):
    """Line item in an invoice."""

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Invoice"),
    )

    product_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Product code"),
        help_text=_("Código de artículo (COD.)"),
    )
    description = models.CharField(max_length=255, verbose_name=_("Description"))
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Quantity")
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Unit price (without tax)")
    )
    line_total = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Line total (without tax)")
    )
    tax_rate = models.ForeignKey(
        "billing.TaxRate",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Tax rate"),
    )
    tax_rate_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Tax rate (%)"),
        help_text=_("Tax percentage at invoice time, e.g. 21.00"),
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Tax amount (line)"),
    )

    class Meta:
        verbose_name = _("Invoice Line Item")
        verbose_name_plural = _("Invoice Line Items")

    def __str__(self):
        return f"{self.invoice} - {self.description}"


# ── Proforma Invoices ─────────────────────────────────────────────────────────


class ProformaInvoice(BaseModel):
    """
    Proforma invoice (pre-invoice / quote with legal value).
    Can be converted to a real Invoice once accepted.
    """

    STATUS_CHOICES = [
        ("draft", _("Borrador")),
        ("sent", _("Enviada")),
        ("accepted", _("Aceptada")),
        ("rejected", _("Rechazada")),
        ("converted", _("Convertida en factura")),
        ("cancelled", _("Cancelada")),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="proforma_invoices",
        verbose_name=_("Customer"),
    )
    converted_to_invoice = models.OneToOneField(
        Invoice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="from_proforma",
        verbose_name=_("Converted to invoice"),
    )

    # Numbering: format YYNNNNN (e.g. 260001 for year 2026, first proforma)
    number = models.IntegerField(verbose_name=_("Proforma number"))
    proforma_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Full proforma number"),
        help_text=_("e.g. 260001"),
    )

    issued_at = models.DateTimeField(verbose_name=_("Issued at"))
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name=_("Status")
    )

    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        verbose_name=_("Subtotal (without tax)"),
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        verbose_name=_("Tax amount"),
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        verbose_name=_("Total (with tax)"),
    )

    # Fiscal snapshot — frozen at issuance
    billing_name_snapshot = models.CharField(max_length=255, blank=True,
        verbose_name=_("Billing name (snapshot)"))
    tax_id_snapshot = models.CharField(max_length=50, blank=True,
        verbose_name=_("Tax ID (snapshot)"))
    billing_address_snapshot = models.TextField(blank=True,
        verbose_name=_("Billing address (snapshot)"))
    customer_code_snapshot = models.CharField(max_length=20, blank=True,
        verbose_name=_("Customer code (snapshot)"))
    customer_phone_snapshot = models.CharField(max_length=30, blank=True,
        verbose_name=_("Customer phone (snapshot)"))
    billing_province_snapshot = models.CharField(max_length=100, blank=True,
        verbose_name=_("Billing province (snapshot)"))

    payment_method = models.CharField(
        max_length=100, blank=True,
        verbose_name=_("Payment method"),
        help_text=_("e.g. TRANSF., GIRO A 30 DIAS"),
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    pdf_file = models.FileField(
        upload_to="proformas/", null=True, blank=True, verbose_name=_("PDF file")
    )

    class Meta:
        verbose_name = _("Proforma Invoice")
        verbose_name_plural = _("Proforma Invoices")
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-issued_at"]),
        ]

    def __str__(self):
        return f"Proforma {self.proforma_number}"

    @classmethod
    def get_next_number(cls, year: int):
        """Return next sequential number for the given year atomically."""
        from django.db import transaction

        prefix = str(year)[-2:]  # last 2 digits: 2026 → "26"
        with transaction.atomic():
            last = (
                cls.objects.select_for_update()
                .filter(proforma_number__startswith=prefix)
                .order_by("-number")
                .first()
            )
            return (last.number + 1) if last else 1

    @classmethod
    def create_number(cls, year: int) -> tuple[int, str]:
        """Return (number, proforma_number) for a new proforma."""
        num = cls.get_next_number(year)
        prefix = str(year)[-2:]
        return num, f"{prefix}{num:04d}"


class ProformaLineItem(BaseModel):
    """Line item in a proforma invoice."""

    proforma = models.ForeignKey(
        ProformaInvoice,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Proforma invoice"),
    )

    product_code = models.CharField(
        max_length=50, blank=True,
        verbose_name=_("Product code"),
        help_text=_("Código de artículo (COD.)"),
    )
    description = models.CharField(max_length=255, verbose_name=_("Description"))
    tono = models.CharField(
        max_length=50, blank=True,
        verbose_name=_("Tono"),
        help_text=_("Color / tono del material"),
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Quantity (UDS.)")
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Unit price (PVP, without tax)")
    )
    line_total = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Line total (without tax)")
    )
    tax_rate = models.ForeignKey(
        "billing.TaxRate",
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name=_("Tax rate"),
    )
    tax_rate_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        verbose_name=_("Tax rate (%)"),
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        verbose_name=_("Tax amount (line)"),
    )

    class Meta:
        verbose_name = _("Proforma Line Item")
        verbose_name_plural = _("Proforma Line Items")

    def __str__(self):
        return f"{self.proforma} - {self.description}"
