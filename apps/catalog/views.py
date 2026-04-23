"""
Views and viewsets for Catalog app.
"""

from django.views.generic import ListView, DetailView
from django.db.models import Prefetch
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


# ── HTML Views ────────────────────────────────────────────────────────────────

class ProductListView(ListView):
    """Catálogo público: listado de productos activos con filtro por categoría."""
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        qs = (
            Product.objects
            .filter(is_active=True)
            .select_related('category', 'brand')
            .prefetch_related(
                Prefetch(
                    'variants',
                    queryset=ProductVariant.objects
                        .filter(is_active=True)
                        .order_by('display_order'),
                )
            )
            .order_by('category__display_order', 'name')
        )
        category_slug = self.request.GET.get('categoria')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = (
            ProductCategory.objects
            .filter(is_active=True)
            .order_by('display_order', 'name')
        )
        context['active_category'] = self.request.GET.get('categoria')
        return context


class ProductDetailView(DetailView):
    """Catálogo público: detalle de un producto con variantes."""
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True)
            .select_related('category', 'brand')
            .prefetch_related(
                Prefetch(
                    'variants',
                    queryset=ProductVariant.objects
                        .filter(is_active=True)
                        .order_by('display_order')
                        .prefetch_related('additional_images'),
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related'] = (
            Product.objects
            .filter(is_active=True, category=self.object.category)
            .exclude(pk=self.object.pk)
            .select_related('category')
            .prefetch_related(
                Prefetch(
                    'variants',
                    queryset=ProductVariant.objects
                        .filter(is_active=True)
                        .order_by('display_order'),
                )
            )[:6]
        )
        return context
