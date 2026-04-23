"""
HTML URL patterns for the public catalog.
Included at /catalogo/ in config/urls/base.py.
"""

from django.urls import path
from .views import ProductListView, ProductDetailView

app_name = 'catalog'

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
]
