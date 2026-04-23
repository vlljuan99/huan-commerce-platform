"""
URLs for Catalog app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, ProductVariantViewSet,
    ProductCategoryViewSet, ProductBrandViewSet
)

app_name = 'catalog'

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='variant')
router.register(r'categories', ProductCategoryViewSet, basename='category')
router.register(r'brands', ProductBrandViewSet, basename='brand')

urlpatterns = [
    path('catalog/', include(router.urls)),
]
