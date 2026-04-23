"""
Views and viewsets for Catalog app.
"""

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, ProductVariant, ProductCategory, ProductBrand
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ProductCategorySerializer, ProductBrandSerializer,
    ProductVariantSerializer
)


class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve product categories."""
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.OrderingFilter]
    ordering = ['display_order', 'name']


class ProductBrandViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve product brands."""
    queryset = ProductBrand.objects.filter(is_active=True)
    serializer_class = ProductBrandSerializer
    lookup_field = 'slug'


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for products.
    List and retrieve products with variants.
    """
    queryset = Product.objects.filter(is_active=True)
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'is_featured']
    search_fields = ['name', 'description', 'sku_base']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use detailed serializer for retrieve, list serializer for list."""
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer


class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for product variants.
    Get available variants for a product.
    """
    queryset = ProductVariant.objects.filter(is_active=True)
    serializer_class = ProductVariantSerializer
    lookup_field = 'sku'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']
