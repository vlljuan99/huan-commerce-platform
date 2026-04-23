from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from apps.catalog.models import Product, ProductVariant
from apps.customers.models import Customer, CustomerAddress
from apps.invoicing.models import Invoice, InvoiceSeries
from apps.orders.models import Order

from .forms import (
    CustomerAddressForm,
    CustomerCreateForm,
    CustomerForm,
    InvoiceCreateForm,
    InvoiceStatusForm,
    OrderCreateForm,
    OrderStatusForm,
    ProductForm,
    ProductVariantForm,
)


class BackofficeRequiredMixin(LoginRequiredMixin):
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.role in ("admin", "commercial")):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


# ── Dashboard ─────────────────────────────────────────────────────────────────

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


# ── Orders ────────────────────────────────────────────────────────────────────

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


class OrderUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/orders/edit.html"
    model = Order
    form_class = OrderStatusForm
    context_object_name = "order"

    def form_valid(self, form):
        messages.success(self.request, f"Pedido {self.object.order_number} actualizado.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:order_detail", kwargs={"pk": self.object.pk})


# ── Customers ─────────────────────────────────────────────────────────────────

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


class CustomerCreateView(BackofficeRequiredMixin, FormView):
    template_name = "backoffice/customers/edit.html"
    form_class = CustomerCreateForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        ctx["page_title"] = "Nuevo cliente"
        return ctx

    def form_valid(self, form):
        customer = form.save()
        messages.success(self.request, f"Cliente {customer} creado correctamente.")
        return redirect("backoffice:customer_detail", pk=customer.pk)


class CustomerUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/customers/edit.html"
    model = Customer
    form_class = CustomerForm
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Editar cliente — {self.object}"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"Cliente {self.object} actualizado.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:customer_detail", kwargs={"pk": self.object.pk})


class CustomerAddressCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/customers/address_edit.html"
    form_class = CustomerAddressForm

    def get_customer(self):
        return get_object_or_404(Customer, pk=self.kwargs["customer_pk"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["customer"] = self.get_customer()
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        address = form.save(commit=False)
        address.customer = self.get_customer()
        address.save()
        messages.success(self.request, "Dirección guardada.")
        return redirect("backoffice:customer_detail", pk=address.customer.pk)


class CustomerAddressUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/customers/address_edit.html"
    model = CustomerAddress
    form_class = CustomerAddressForm
    context_object_name = "address"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["customer"] = self.object.customer
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Dirección actualizada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "backoffice:customer_detail", kwargs={"pk": self.object.customer.pk}
        )


# ── Invoices ──────────────────────────────────────────────────────────────────

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


class InvoiceUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/invoices/edit.html"
    model = Invoice
    form_class = InvoiceStatusForm
    context_object_name = "invoice"

    def form_valid(self, form):
        messages.success(
            self.request, f"Factura {self.object.invoice_number} actualizada."
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:invoice_detail", kwargs={"pk": self.object.pk})


# ── Catalog ───────────────────────────────────────────────────────────────────

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


class ProductCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/catalog/edit.html"
    model = Product
    form_class = ProductForm
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Producto "{form.instance.name}" creado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:product_edit", kwargs={"pk": self.object.pk})


class ProductUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/catalog/edit.html"
    model = Product
    form_class = ProductForm
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.prefetch_related("variants__additional_images")

    def form_valid(self, form):
        messages.success(self.request, f'Producto "{self.object.name}" actualizado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:product_edit", kwargs={"pk": self.object.pk})


class ProductVariantCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/catalog/variant_edit.html"
    form_class = ProductVariantForm

    def get_product(self):
        return get_object_or_404(Product, pk=self.kwargs["product_pk"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = self.get_product()
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        variant = form.save(commit=False)
        variant.product = self.get_product()
        variant.save()
        messages.success(self.request, f'Variante "{variant.name}" creada.')
        return redirect("backoffice:product_edit", pk=variant.product.pk)


class ProductVariantUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/catalog/variant_edit.html"
    model = ProductVariant
    form_class = ProductVariantForm
    context_object_name = "variant"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = self.object.product
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Variante "{self.object.name}" actualizada.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "backoffice:product_edit", kwargs={"pk": self.object.product.pk}
        )


# ── Invoice create ────────────────────────────────────────────────────────────

class InvoiceCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/invoices/create.html"
    form_class = InvoiceCreateForm

    def form_valid(self, form):
        invoice = form.save(commit=False)
        series = form.cleaned_data["series"]
        num = series.get_next_number()
        year = (
            invoice.issued_at.year
            if invoice.issued_at
            else timezone.now().year
        )
        invoice.number = num
        invoice.invoice_number = f"{series.prefix}-{year}-{num:04d}"
        # Billing snapshots from customer
        customer = form.cleaned_data["customer"]
        invoice.billing_name_snapshot = customer.billing_name
        invoice.tax_id_snapshot = customer.tax_id or ""
        invoice.status = "draft"
        invoice.save()
        messages.success(
            self.request, f"Factura {invoice.invoice_number} creada."
        )
        return redirect("backoffice:invoice_detail", pk=invoice.pk)


# ── Order create ──────────────────────────────────────────────────────────────

class OrderCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/orders/create.html"
    form_class = OrderCreateForm

    def form_valid(self, form):
        order = form.save(commit=False)
        year = timezone.now().year
        last = (
            Order.objects.filter(order_number__startswith=f"ORD-{year}-")
            .order_by("-order_number")
            .first()
        )
        try:
            n = int(last.order_number.split("-")[-1]) + 1 if last else 1
        except (ValueError, IndexError):
            n = 1
        order.order_number = f"ORD-{year}-{n:04d}"
        order.status = "draft"
        order.save()
        messages.success(
            self.request, f"Pedido {order.order_number} creado."
        )
        return redirect("backoffice:order_detail", pk=order.pk)
