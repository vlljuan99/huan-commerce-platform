import io
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import DetailView, FormView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

logger = logging.getLogger(__name__)

from apps.catalog.models import Product, ProductVariant, ProductCategory, ProductBrand, CatalogPDF
from apps.customers.models import Customer, CustomerAddress
from apps.invoicing.models import Invoice, InvoiceSeries
from apps.orders.models import Order
from apps.services.models import Company, ServiceCategory, Service

from .forms import (
    CatalogPDFForm,
    CompanyForm,
    CustomerAddressForm,
    CustomerCreateForm,
    CustomerForm,
    InvoiceCreateForm,
    InvoiceStatusForm,
    OrderCreateForm,
    OrderStatusForm,
    ProductCategoryForm,
    ProductBrandForm,
    ProductForm,
    ProductVariantForm,
    ServiceCategoryForm,
    ServiceForm,
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
        sort_map = {
            "number": "order_number",
            "customer": "customer__user__email",
            "status": "status",
            "total": "total",
            "date": "created_at",
        }
        sort = self.request.GET.get("sort", "date")
        direction = self.request.GET.get("dir", "desc")
        order_field = sort_map.get(sort, "created_at")
        prefix = "" if direction == "asc" else "-"
        qs = Order.objects.select_related("customer__user").order_by(f"{prefix}{order_field}")
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
        ctx["current_sort"] = self.request.GET.get("sort", "date")
        ctx["current_dir"] = self.request.GET.get("dir", "desc")
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
        sort_map = {
            "name": "user__last_name",
            "email": "user__email",
            "company": "company_name",
            "segment": "segment",
            "date": "created_at",
        }
        sort = self.request.GET.get("sort", "date")
        direction = self.request.GET.get("dir", "desc")
        order_field = sort_map.get(sort, "created_at")
        prefix = "" if direction == "asc" else "-"
        qs = Customer.objects.select_related("user").order_by(f"{prefix}{order_field}")
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
        ctx["current_sort"] = self.request.GET.get("sort", "date")
        ctx["current_dir"] = self.request.GET.get("dir", "desc")
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
        sort_map = {
            "number": "invoice_number",
            "customer": "customer__user__email",
            "status": "status",
            "total": "total",
            "date": "issued_at",
            "due": "due_date",
        }
        sort = self.request.GET.get("sort", "date")
        direction = self.request.GET.get("dir", "desc")
        order_field = sort_map.get(sort, "issued_at")
        prefix = "" if direction == "asc" else "-"
        qs = Invoice.objects.select_related("customer__user", "series").order_by(
            f"{prefix}{order_field}"
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
        ctx["current_sort"] = self.request.GET.get("sort", "date")
        ctx["current_dir"] = self.request.GET.get("dir", "desc")
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
        sort_map = {
            "name": "name",
            "category": "category__name",
            "brand": "brand__name",
            "status": "is_active",
        }
        sort = self.request.GET.get("sort", "name")
        direction = self.request.GET.get("dir", "asc")
        order_field = sort_map.get(sort, "name")
        prefix = "" if direction == "asc" else "-"
        qs = (
            Product.objects.select_related("category", "brand")
            .prefetch_related("variants")
            .order_by(f"{prefix}{order_field}")
        )
        q = self.request.GET.get("q", "").strip()
        category_pk = self.request.GET.get("category", "")
        brand_pk = self.request.GET.get("brand", "")
        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(sku_base__icontains=q)
        if category_pk:
            qs = qs.filter(category__pk=category_pk)
        if brand_pk:
            qs = qs.filter(brand__pk=brand_pk)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["current_sort"] = self.request.GET.get("sort", "name")
        ctx["current_dir"] = self.request.GET.get("dir", "asc")
        ctx["current_category"] = self.request.GET.get("category", "")
        ctx["current_brand"] = self.request.GET.get("brand", "")
        ctx["category_list"] = ProductCategory.objects.filter(is_active=True).order_by("name")
        ctx["brand_list"] = ProductBrand.objects.filter(is_active=True).order_by("name")
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


# ── Categories ───────────────────────────────────────────────────────────────

class CategoryListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/catalog/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        sort_map = {"name": "name", "order": "display_order", "status": "is_active"}
        sort = self.request.GET.get("sort", "order")
        direction = self.request.GET.get("dir", "asc")
        order_field = sort_map.get(sort, "display_order")
        prefix = "" if direction == "asc" else "-"
        return ProductCategory.objects.select_related("parent").order_by(f"{prefix}{order_field}", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_sort"] = self.request.GET.get("sort", "order")
        ctx["current_dir"] = self.request.GET.get("dir", "asc")
        return ctx


class CategoryCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/catalog/category_edit.html"
    form_class = ProductCategoryForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.name}" creada.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:category_list")


class CategoryUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/catalog/category_edit.html"
    model = ProductCategory
    form_class = ProductCategoryForm
    context_object_name = "category"

    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{self.object.name}" actualizada.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:category_list")


# ── Brands ────────────────────────────────────────────────────────────────────

class BrandListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/catalog/brand_list.html"
    context_object_name = "brands"

    def get_queryset(self):
        sort_map = {"name": "name", "status": "is_active"}
        sort = self.request.GET.get("sort", "name")
        direction = self.request.GET.get("dir", "asc")
        order_field = sort_map.get(sort, "name")
        prefix = "" if direction == "asc" else "-"
        return ProductBrand.objects.order_by(f"{prefix}{order_field}")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_sort"] = self.request.GET.get("sort", "name")
        ctx["current_dir"] = self.request.GET.get("dir", "asc")
        return ctx


class BrandCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/catalog/brand_edit.html"
    form_class = ProductBrandForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Marca "{form.instance.name}" creada.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:brand_list")


class BrandUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/catalog/brand_edit.html"
    model = ProductBrand
    form_class = ProductBrandForm
    context_object_name = "brand"

    def form_valid(self, form):
        messages.success(self.request, f'Marca "{self.object.name}" actualizada.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:brand_list")


# ── Catalog PDFs ──────────────────────────────────────────────────────────────

class CatalogPDFListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/catalog/pdf_list.html"
    context_object_name = "catalogs"

    def get_queryset(self):
        return CatalogPDF.objects.select_related("brand").order_by("-year", "title")


class CatalogPDFCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/catalog/pdf_edit.html"
    form_class = CatalogPDFForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Catálogo "{form.instance.title}" creado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:catalogpdf_list")


class CatalogPDFUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/catalog/pdf_edit.html"
    model = CatalogPDF
    form_class = CatalogPDFForm
    context_object_name = "catalog"

    def form_valid(self, form):
        messages.success(self.request, f'Catálogo "{self.object.title}" actualizado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:catalogpdf_list")


class CatalogPDFDeleteView(BackofficeRequiredMixin, DeleteView):
    model = CatalogPDF
    success_url = reverse_lazy("backoffice:catalogpdf_list")

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Catálogo "{obj.title}" eliminado.')
        return super().delete(request, *args, **kwargs)


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


# ── Services ──────────────────────────────────────────────────────────────────

class ServiceListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/services/list.html"
    context_object_name = "services"
    paginate_by = 30

    def get_queryset(self):
        qs = Service.objects.select_related("category", "company")
        sort_map = {"name": "name", "category": "category__name", "status": "is_active"}
        sort = self.request.GET.get("sort", "name")
        direction = self.request.GET.get("dir", "asc")
        order_field = sort_map.get(sort, "name")
        prefix = "" if direction == "asc" else "-"
        qs = qs.order_by(f"{prefix}{order_field}")
        category_pk = self.request.GET.get("category")
        if category_pk:
            qs = qs.filter(category_id=category_pk)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_sort"] = self.request.GET.get("sort", "name")
        ctx["current_dir"] = self.request.GET.get("dir", "asc")
        ctx["category_list"] = ServiceCategory.objects.filter(is_active=True)
        ctx["current_category"] = self.request.GET.get("category", "")
        return ctx


class ServiceCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/services/edit.html"
    model = Service
    form_class = ServiceForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Servicio "{form.instance.name}" creado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:service_edit", kwargs={"pk": self.object.pk})


class ServiceUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/services/edit.html"
    model = Service
    form_class = ServiceForm

    def form_valid(self, form):
        messages.success(self.request, f'Servicio "{self.object.name}" actualizado.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:service_edit", kwargs={"pk": self.object.pk})


# ── Service categories ────────────────────────────────────────────────────────

class ServiceCategoryListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/services/category_list.html"
    context_object_name = "categories"
    queryset = ServiceCategory.objects.all().order_by("display_order", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_sort"] = self.request.GET.get("sort", "order")
        ctx["current_dir"] = self.request.GET.get("dir", "asc")
        return ctx


class ServiceCategoryCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/services/category_edit.html"
    model = ServiceCategory
    form_class = ServiceCategoryForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{form.instance.name}" creada.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:service_category_list")


class ServiceCategoryUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/services/category_edit.html"
    model = ServiceCategory
    form_class = ServiceCategoryForm

    def form_valid(self, form):
        messages.success(self.request, f'Categoría "{self.object.name}" actualizada.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:service_category_list")


# ── Companies ─────────────────────────────────────────────────────────────────

class CompanyListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/services/company_list.html"
    context_object_name = "companies"
    queryset = Company.objects.all().order_by("-is_own", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_sort"] = self.request.GET.get("sort", "name")
        ctx["current_dir"] = self.request.GET.get("dir", "asc")
        return ctx


class CompanyCreateView(BackofficeRequiredMixin, CreateView):
    template_name = "backoffice/services/company_edit.html"
    model = Company
    form_class = CompanyForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f'Empresa "{form.instance.name}" creada.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:company_edit", kwargs={"pk": self.object.pk})


class CompanyUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/services/company_edit.html"
    model = Company
    form_class = CompanyForm

    def form_valid(self, form):
        messages.success(self.request, f'Empresa "{self.object.name}" actualizada.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("backoffice:company_edit", kwargs={"pk": self.object.pk})


# ── Visualiza tu Obra (IA) ─────────────────────────────────────────────────────

def _to_png_bytes(upload_file) -> bytes:
    """Convierte un fichero subido a bytes PNG con canal alfa."""
    from PIL import Image
    upload_file.seek(0)
    with Image.open(upload_file) as img:
        buf = io.BytesIO()
        img.convert("RGBA").save(buf, format="PNG")
        return buf.getvalue()


def _build_reforma_prompt(color_hex: str, has_tile: bool) -> str:
    tile_part = (
        "Sustituye el suelo por un material cerámico basado en la imagen de azulejo "
        "proporcionada como referencia. Ajusta el patrón del suelo a la perspectiva real "
        "(escala, orientación y repetición correctas). "
        "Mantén realismo en juntas, textura y acabado (mate/brillo). "
    ) if has_tile else (
        "No modifiques el suelo. "
    )
    return (
        "Actúa como un sistema de visualización arquitectónica profesional. "
        "Modifica la imagen de la habitación siguiendo estas reglas estrictamente:\n"
        "- Mantén intactos muebles, electrodomésticos, encimera, ventanas, puertas, "
        "iluminación, sombras, perspectiva y distribución.\n"
        f"- Cambia el color de las paredes a {color_hex}. Aplica el color de forma "
        "uniforme respetando sombras e iluminación natural.\n"
        f"- {tile_part}"
        "- Integra correctamente el nuevo suelo con la iluminación existente. "
        "Ajusta sombras y reflejos en función del nuevo material.\n"
        "- No introduzcas nuevos elementos decorativos. No alteres el estilo de la habitación.\n"
        "- Evita artefactos visuales o deformaciones.\n"
        "El resultado debe ser completamente fotorrealista, como una fotografía real "
        "tomada después de una reforma."
    )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class VisualizaObraView(BackofficeRequiredMixin, TemplateView):
    template_name = "backoffice/visualiza_obra.html"

    _ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
    _MAX_SIZE = 20 * 1024 * 1024  # 20 MB

    def post(self, request, *args, **kwargs):
        try:
            import openai
        except ImportError:
            return JsonResponse(
                {"error": "La librería openai no está instalada. Ejecuta: pip install openai"},
                status=500,
            )

        from decouple import config as decouple_config
        api_key = decouple_config("OPENAI_API_KEY", default="").strip()
        if not api_key:
            return JsonResponse(
                {"error": "OPENAI_API_KEY no está configurada en el fichero .env"},
                status=500,
            )

        room_file = request.FILES.get("room_image")
        tile_file = request.FILES.get("tile_image")
        wall_color = request.POST.get("wall_color", "#FFFFFF").strip()

        # ── Validaciones ──────────────────────────────────────────────────────
        if not room_file:
            return JsonResponse({"error": "Debes subir una imagen de la habitación."}, status=400)

        if not (wall_color.startswith("#") and len(wall_color) in (4, 7)):
            return JsonResponse(
                {"error": "Color de pared no válido. Usa formato #RRGGBB."}, status=400
            )

        for label, f in [("habitación", room_file), ("azulejo", tile_file)]:
            if f is None:
                continue
            if f.content_type not in self._ALLOWED_TYPES:
                return JsonResponse(
                    {"error": f"Formato de imagen de {label} no válido. Usa PNG, JPEG o WebP."},
                    status=400,
                )
            if f.size > self._MAX_SIZE:
                return JsonResponse(
                    {"error": f"La imagen de {label} supera el límite de 20 MB."},
                    status=400,
                )

        # ── Llamada a la API ───────────────────────────────────────────────────
        try:
            client = openai.OpenAI(api_key=api_key)

            room_png = _to_png_bytes(room_file)
            images_param = [("room.png", room_png, "image/png")]

            if tile_file:
                tile_png = _to_png_bytes(tile_file)
                images_param.append(("tile.png", tile_png, "image/png"))

            prompt = _build_reforma_prompt(wall_color, has_tile=tile_file is not None)

            # gpt-image-1 acepta lista de imágenes en el parámetro image
            image_files = [
                (name, io.BytesIO(data), mime)
                for name, data, mime in images_param
            ]

            response = client.images.edit(
                model="gpt-image-1",
                image=image_files if len(image_files) > 1 else image_files[0],
                prompt=prompt,
                n=2,
                size="1024x1024",
            )

            result_images = []
            for item in response.data:
                if getattr(item, "b64_json", None):
                    result_images.append({"type": "b64", "data": item.b64_json})
                elif getattr(item, "url", None):
                    result_images.append({"type": "url", "data": item.url})

            return JsonResponse({"images": result_images})

        except openai.OpenAIError as exc:
            logger.error("OpenAI API error en VisualizaObraView: %s", exc)
            return JsonResponse({"error": f"Error de la API de OpenAI: {exc}"}, status=502)
        except Exception:
            logger.exception("Error inesperado en VisualizaObraView")
            return JsonResponse({"error": "Error interno del servidor."}, status=500)

