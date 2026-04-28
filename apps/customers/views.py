"""
Views and viewsets for Customers app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Customer, CustomerAddress
from .serializers import CustomerSerializer, CustomerAddressSerializer


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Customer profile (read-only).
    Only authenticated users can see their own profile.
    """

    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's customer profile."""
        user = self.request.user
        return Customer.objects.filter(user=user)

    @action(detail=False, methods=["get"])
    def my_profile(self, request):
        """Get current user's customer profile."""
        try:
            customer = Customer.objects.get(user=request.user)
            serializer = self.get_serializer(customer)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {"detail": "Customer profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def addresses(self, request):
        """Get all addresses for the current user."""
        try:
            customer = Customer.objects.get(user=request.user)
            addresses = customer.addresses.all()
            serializer = CustomerAddressSerializer(addresses, many=True)
            return Response(serializer.data)
        except Customer.DoesNotExist:
            return Response(
                {"detail": "Customer profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class CustomerAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CustomerAddress.
    Only allows CRUD on own addresses.
    """

    serializer_class = CustomerAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's addresses."""
        try:
            customer = Customer.objects.get(user=self.request.user)
            return CustomerAddress.objects.filter(customer=customer)
        except Customer.DoesNotExist:
            return CustomerAddress.objects.none()

    def perform_create(self, serializer):
        """Automatically set the customer on creation."""
        customer = Customer.objects.get(user=self.request.user)
        serializer.save(customer=customer)
