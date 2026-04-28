"""
Serializers for Invoicing app.
"""

from rest_framework import serializers
from .models import Invoice, InvoiceLineItem


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    tax_rate_name = serializers.CharField(source="tax_rate.name", read_only=True)

    class Meta:
        model = InvoiceLineItem
        fields = [
            "id",
            "description",
            "quantity",
            "unit_price",
            "line_total",
            "tax_rate",
            "tax_rate_name",
        ]
        read_only_fields = ["id", "line_total"]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceLineItemSerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "customer_name",
            "status",
            "issued_at",
            "subtotal",
            "tax_amount",
            "total",
            "items",
            "pdf_file",
            "created_at",
        ]
        read_only_fields = ["id", "invoice_number", "total", "created_at"]

    def get_customer_name(self, obj):
        return str(obj.customer)
