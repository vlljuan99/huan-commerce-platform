"""
Views and viewsets for Invoicing app.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Invoices (read-only).
    Only authenticated customers can see their own invoices.
    Provides PDF download endpoint.
    """

    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only the current user's invoices."""
        user = self.request.user
        return Invoice.objects.filter(customer__user=user)

    @action(detail=False, methods=["get"])
    def my_invoices(self, request):
        """Get all invoices for the current user."""
        invoices = self.get_queryset()
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def download_pdf(self, request, pk=None):
        """Download invoice PDF."""
        invoice = self.get_object()
        if not invoice.pdf_file:
            return Response(
                {"detail": "PDF not available for this invoice."},
                status=status.HTTP_404_NOT_FOUND,
            )
        response = FileResponse(
            invoice.pdf_file.open("rb"), content_type="application/pdf"
        )
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{invoice.invoice_number}.pdf"'
        return response
