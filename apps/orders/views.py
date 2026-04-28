"""
Views and viewsets for Orders app.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Orders (read-only).
    Only authenticated customers can see their own orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's orders."""
        user = self.request.user
        return Order.objects.filter(customer__user=user)

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Get all orders for the current user."""
        orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def order_detail(self, request, pk=None):
        """Get detailed view of a specific order."""
        order = self.get_object()
        serializer = self.get_serializer(order)
        return Response(serializer.data)
