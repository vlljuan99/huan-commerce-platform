"""
Serializers for Customers app.
"""

from rest_framework import serializers
from .models import Customer, CustomerAddress


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = [
            "id",
            "name",
            "address_type",
            "street_address",
            "city",
            "postal_code",
            "region",
            "country",
            "is_default",
            "full_address",
        ]
        read_only_fields = ["id", "full_address"]


class CustomerSerializer(serializers.ModelSerializer):
    addresses = CustomerAddressSerializer(many=True, read_only=True)
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "id",
            "user_name",
            "user_email",
            "company_name",
            "tax_id",
            "phone",
            "segment",
            "addresses",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_user_name(self, obj):
        return obj.user.get_full_name()

    def get_user_email(self, obj):
        return obj.user.email
