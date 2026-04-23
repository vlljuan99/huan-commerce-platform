"""
Serializers for Orders app.
"""

from rest_framework import serializers
from .models import Order, OrderLineItem


class OrderLineItemSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(
        source='variant.name',
        read_only=True
    )
    product_name = serializers.CharField(
        source='variant.product.name',
        read_only=True
    )

    class Meta:
        model = OrderLineItem
        fields = [
            'id', 'variant', 'variant_name', 'product_name',
            'quantity', 'unit_price', 'line_total'
        ]
        read_only_fields = ['id', 'line_total']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderLineItemSerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'status',
            'subtotal', 'tax_amount', 'shipping_cost', 'total',
            'items', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'order_number', 'total', 'created_at']

    def get_customer_name(self, obj):
        return str(obj.customer)
