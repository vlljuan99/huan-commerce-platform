"""
Catalog serializers for REST API.
"""

from rest_framework import serializers
from .models import Product, ProductVariant, ProductCategory, ProductBrand


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "slug", "description"]


class ProductBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBrand
        fields = ["id", "name", "slug", "description", "logo"]


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "name",
            "price_no_tax",
            "stock_quantity",
            "image",
            "is_in_stock",
        ]
        read_only_fields = ["id", "is_in_stock"]


class ProductListSerializer(serializers.ModelSerializer):
    """Minimal serializer for product listings."""

    category = ProductCategorySerializer(read_only=True)
    brand = ProductBrandSerializer(read_only=True)
    primary_variant = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "brand",
            "sku_base",
            "is_featured",
            "primary_variant",
        ]
        read_only_fields = fields

    def get_primary_variant(self, obj):
        """Get the first active variant."""
        variant = obj.variants.filter(is_active=True).first()
        return ProductVariantSerializer(variant).data if variant else None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed product serializer with all variants."""

    category = ProductCategorySerializer(read_only=True)
    brand = ProductBrandSerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "category",
            "brand",
            "sku_base",
            "unit_of_measure",
            "weight",
            "is_featured",
            "seo_title",
            "seo_description",
            "variants",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
