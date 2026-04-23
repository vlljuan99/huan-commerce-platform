from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from apps.catalog.models import Product
from apps.customers.models import Customer
from apps.invoicing.models import Invoice
from apps.orders.models import Order


class BackofficeRequiredMixin(LoginRequiredMixin):
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.role in ("admin", "commercial")):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class DashboardView(BackofficeRequiredMixin, TemplateView):
    template_name = "backoffice/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        month_start = today.replace(day=1)
        confirmed = ["confirmed", "processing", "shipped", "delivered"]
        ctx["orders_total"] = Order.objects.count()
        ctx["orders_pending"] = Order.objects.filter(
            status__in=["pending", "confirmed", "processing"]
        ).count()
        ctx["revenue_month"] = (
            Order.objects.filter(
                created_at__date__gte=month_start, status__in=confirmed
            ).aggregate(t=Sum("total"))["t"]
            or 0
        )
        ctx["customers_total"] = Customer.objects.count()
        ctx["customers_b2b"] = Customer.objects.filter(segment="b2b").count()
        ctx["invoices_pending"] = Invoice.objects.filter(
            status__in=["draft", "issued"]
        ).count()
        ctx["invoices_overdue"] = Invoice.objects.filter(status="overdue").count()
        ctx["recent_orders"] = (
            Order.objects.select_related("customer__user").order_by("-created_at")[:10]
        )
        ctx["recent_invoices"] = (
            Invoice.objects.select_related("customer__user").order_by("-issued_at")[:5]
        )
        return ctx


class OrderListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/orders/list.html"
    context_object_name = "orders"
    paginate_by = 25

    def get_queryset(self):
        qs = Order.objects.select_related("customer__user").order_by("-created_at")
        status = self.request.GET.get("status")
        q = self.request.GET.get("q", "").strip()
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(order_number__icontains=q) | qs.filter(
                customer__user__email__icontains=q
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Order.STATUS_CHOICES
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class OrderDetailView(BackofficeRequiredMixin, DetailView):
    template_name = "backoffice/orders/detail.html"
    model = Order
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related("customer__user").prefetch_related("items")


class CustomerListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/customers/list.html"
    context_object_name = "customers"
    paginate_by = 25

    def get_queryset(self):
        qs = Customer.objects.select_related("user").order_by("-created_at")
        segment = self.request.GET.get("segment")
        q = self.request.GET.get("q", "").strip()
        if segment:
            qs = qs.filter(segment=segment)
        if q:
            qs = (
                qs.filter(user__email__icontains=q)
                | qs.filter(company_name__icontains=q)
                | qs.filter(tax_id__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["segment_choices"] = Customer.SEGMENT_CHOICES
        ctx["current_segment"] = self.request.GET.get("segment", "")
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class CustomerDetailView(BackofficeRequiredMixin, DetailView):
    template_name = "backoffice/customers/detail.html"
    model = Customer
    context_object_name = "customer"

    def get_queryset(self):
        return Customer.objects.select_related("user").prefetch_related(
            "addresses", "orders", "invoices"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["recent_orders"] = self.object.orders.order_by("-created_at")[:10]
        ctx["recent_invoices"] = self.object.invoices.order_by("-issued_at")[:10]
        return ctx


class InvoiceListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/invoices/list.html"
    context_object_name = "invoices"
    paginate_by = 25

    def get_queryset(self):
        qs = Invoice.objects.select_related("customer__user", "series").order_by(
            "-issued_at"
        )
        status = self.request.GET.get("status")
        q = self.request.GET.get("q", "").strip()
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(invoice_number__icontains=q) | qs.filter(
                customer__user__email__icontains=q
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Invoice.STATUS_CHOICES
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class InvoiceDetailView(BackofficeRequiredMixin, DetailView):
    template_name = "backoffice/invoices/detail.html"
    model = Invoice
    context_object_name = "invoice"

    def get_queryset(self):
        return Invoice.objects.select_related(
            "customer__user", "series", "order"
        ).prefetch_related("items__tax_rate")


class CatalogListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/catalog/list.html"
    context_object_name = "products"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Product.objects.select_related("category", "brand")
            .prefetch_related("variants")
            .order_by("category__name", "name")
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(sku_base__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx
