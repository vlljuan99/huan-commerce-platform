"""
HTML URL patterns for the public catalog and PDF catalog pages.
"""

from django.urls import path
from .views import ProductListView, ProductDetailView, CatalogPDFListView

app_name = "catalog"

urlpatterns = [
    path("productos/", ProductListView.as_view(), name="product_list"),
    path("productos/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
    path("catalogos/", CatalogPDFListView.as_view(), name="catalog_pdf_list"),
]
