"""
URLs for Customers app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, CustomerAddressViewSet

app_name = 'customers'

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'addresses', CustomerAddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]
