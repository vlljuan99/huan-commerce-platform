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
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from apps.catalog.models import (
    Product,
    ProductVariant,
    ProductCategory,
    ProductBrand,
    CatalogPDF,
)
from apps.customers.models import Customer, CustomerAddress
from apps.invoicing.models import Invoice, ProformaInvoice
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

logger = logging.getLogger(__name__)


class BackofficeRequiredMixin(LoginRequiredMixin):
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (
            request.user.is_superuser or request.user.role in ("admin", "commercial")
        ):
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
        ctx["recent_orders"] = Order.objects.select_related("customer__user").order_by(
            "-created_at"
        )[:10]
        ctx["recent_invoices"] = Invoice.objects.select_related(
            "customer__user"
        ).order_by("-issued_at")[:5]
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
        qs = Order.objects.select_related("customer__user").order_by(
            f"{prefix}{order_field}"
        )
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
        messages.success(
            self.request, f"Pedido {self.object.order_number} actualizado."
        )
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


class InvoiceGeneratePDFView(BackofficeRequiredMixin, View):
    """
    Generate a PDF for a regular invoice (FACTURA DE VENTA).
    Layout matches the Fra H6 reference document.
    """

    def post(self, request, pk):
        import io
        import os
        import textwrap
        from django.conf import settings
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from apps.core.instance import get_branding, get_profile

        invoice = get_object_or_404(
            Invoice.objects.select_related("customer__user", "series", "order")
            .prefetch_related("items__tax_rate"),
            pk=pk,
        )

        branding = get_branding()
        footer = branding.get("footer", {})

        W, H = A4  # 595 x 842 pt
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setLineWidth(0.5)

        instance_id = get_profile().get("instance_id", "")
        logo_path = os.path.join(
            settings.BASE_DIR, "instances", instance_id,
            "static", instance_id, "logo_blanco.png",
        )

        # ── HEADER ────────────────────────────────────────────────────────────
        # Left: company text block
        y = H - 28
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30, y, footer.get("legal_name") or footer.get("company_name", ""))
        y -= 13
        c.setFont("Helvetica", 8.5)
        if footer.get("tax_id"):
            c.drawString(30, y, f"C.I.F.: {footer['tax_id']}")
            y -= 12
        if footer.get("address"):
            c.drawString(30, y, footer["address"])
            y -= 12
        if footer.get("zip") and footer.get("city"):
            city_line = f"{footer['zip']} {footer['city']}"
            if footer.get("province"):
                city_line += f" ({footer['province']})"
            c.drawString(30, y, city_line)
            y -= 12
        if footer.get("phone"):
            c.drawString(30, y, f"Tlf. {footer['phone']}")
            y -= 12
        if footer.get("email"):
            c.drawString(30, y, footer["email"])

        # Center: QR placeholder
        qr_x, qr_y, qr_w, qr_h = 212, H - 105, 85, 82
        c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(qr_x + qr_w / 2, H - 22, "QR tributario:")
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        c.rect(qr_x, qr_y, qr_w, qr_h, stroke=1, fill=1)
        # Simple QR-like inner pattern (placeholder)
        c.setFillColor(colors.HexColor("#dddddd"))
        cell = 8
        for row in range(9):
            for col in range(9):
                if (row + col) % 2 == 0:
                    c.rect(qr_x + 4 + col * cell, qr_y + 4 + row * cell, cell - 1, cell - 1, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(qr_x + qr_w / 2, qr_y - 10, "VERI*FACTU")

        # Right: logo + title
        logo_drawn = False
        if os.path.isfile(logo_path):
            try:
                c.drawImage(logo_path, 315, H - 78, width=120, height=52,
                            preserveAspectRatio=True, mask="auto")
                logo_drawn = True
            except Exception:
                pass
        if not logo_drawn:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(315, H - 55, footer.get("company_name", ""))
        c.setFont("Helvetica-Bold", 13)
        c.drawString(315, H - 95, "FACTURA DE VENTA")

        # ── SEPARATOR ────────────────────────────────────────────────────────
        c.setStrokeColor(colors.black)
        c.line(30, H - 108, W - 30, H - 108)

        # ── CLIENT BOX (left) + INVOICE DATA BOX (right) ─────────────────────
        box_top = H - 112
        box_h = 88
        box_bottom = box_top - box_h

        # Left box: client data
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        c.rect(30, box_bottom, 252, box_h, stroke=1, fill=0)

        addr_lines = [l.strip() for l in invoice.billing_address_snapshot.splitlines() if l.strip()]
        street = addr_lines[0] if len(addr_lines) > 0 else ""
        postal_city = addr_lines[1] if len(addr_lines) > 1 else ""

        left_rows = [
            ("CLIENTE:", invoice.billing_name_snapshot or str(invoice.customer)),
            ("DIRECCION:", street),
            ("C.P. / POBLACION:", postal_city),
            ("PROVINCIA:", invoice.billing_province_snapshot),
        ]
        ry = box_top - 14
        for label, value in left_rows:
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.black)
            c.drawString(34, ry, label)
            c.setFont("Helvetica", 8)
            c.drawString(120, ry, str(value)[:38])
            ry -= 14

        # Right box: invoice metadata
        c.setFillColor(colors.white)
        c.rect(290, box_bottom, 275, box_h, stroke=1, fill=0)

        right_rows = [
            ("Nº FACTURA:", invoice.invoice_number),
            ("FECHA:", invoice.issued_at.strftime("%d/%m/%Y")),
            ("COD. CLIENTE:", invoice.customer_code_snapshot),
            ("CIF.:", invoice.tax_id_snapshot),
            ("TELEFONO:", invoice.customer_phone_snapshot),
            ("FORMA PAGO:", invoice.payment_method),
        ]
        ry = box_top - 14
        for label, value in right_rows:
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.black)
            c.drawString(294, ry, label)
            c.setFont("Helvetica", 8)
            c.drawString(390, ry, str(value)[:28])
            ry -= 14

        # ── LINE ITEMS TABLE ──────────────────────────────────────────────────
        # Columns: CANTIDAD(60) | DESCRIPCION(290) | PRECIO(85) | IMPORTE(100)
        COL_X = [30, 90, 380, 465]  # left edge of each column
        COL_W = [60, 290, 85, 100]
        TH = box_bottom - 15  # table header top

        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        c.rect(30, TH - 17, W - 60, 17, stroke=1, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        headers = ["CANTIDAD", "DESCRIPCION", "PRECIO", "IMPORTE"]
        for i, h in enumerate(headers):
            c.drawString(COL_X[i] + 3, TH - 12, h)

        y = TH - 17
        c.setFillColor(colors.black)
        row = 0
        for item in invoice.items.all():
            if row % 2 == 0:
                c.setFillColor(colors.HexColor("#f3f4f6"))
                c.rect(30, y - 15, W - 60, 15, stroke=0, fill=1)
                c.setFillColor(colors.black)
            c.setFont("Helvetica", 8.5)
            c.drawString(COL_X[0] + 3, y - 10, f"{item.quantity:,.2f}".replace(",", "."))
            desc = str(item.description)
            c.drawString(COL_X[1] + 3, y - 10, desc[:52] + ("..." if len(desc) > 52 else ""))
            c.drawRightString(COL_X[2] + COL_W[2] - 3, y - 10, f"{item.unit_price:,.2f}".replace(",", "."))
            c.drawRightString(COL_X[3] + COL_W[3] - 3, y - 10, f"{item.line_total:,.2f}".replace(",", "."))
            y -= 15
            row += 1

        # ── BOTTOM SECTION ────────────────────────────────────────────────────
        # Totals (right side) and bank info (left side) side by side
        totals_y = y - 12
        c.setStrokeColor(colors.black)
        c.line(30, y - 5, W - 30, y - 5)

        # Right: totals box
        tx = 370
        ty = totals_y
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)

        c.setFillColor(colors.HexColor("#f3f4f6"))
        c.rect(tx, ty - 17, W - 30 - tx, 17, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(tx + 4, ty - 12, "SUBTOTAL")
        c.drawRightString(W - 33, ty - 12, f"{invoice.subtotal:,.2f}".replace(",", "."))
        ty -= 17

        # IVA lines — group by rate
        from collections import defaultdict
        iva_groups: dict = defaultdict(lambda: {"base": 0, "tax": 0})
        for item in invoice.items.all():
            pct = float(item.tax_rate_pct)
            iva_groups[pct]["base"] += float(item.line_total)
            iva_groups[pct]["tax"] += float(item.tax_amount)

        for pct, vals in sorted(iva_groups.items()):
            c.setFillColor(colors.white)
            c.rect(tx, ty - 17, W - 30 - tx, 17, stroke=1, fill=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawString(tx + 4, ty - 12, f"IVA ({pct:.0f} %)")
            c.drawRightString(W - 33, ty - 12, f"{vals['tax']:,.2f}".replace(",", "."))
            ty -= 17

        c.setFillColor(colors.black)
        c.rect(tx, ty - 20, W - 30 - tx, 20, stroke=1, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(tx + 4, ty - 14, "TOTAL €")
        c.drawRightString(W - 33, ty - 14, f"{invoice.total:,.2f}".replace(",", "."))

        # Left: bank info
        bx = 30
        by = totals_y
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(bx, by - 12, "BANCO:")
        by -= 14
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(bx, by - 12, "Nº CUENTA:")
        c.setFont("Helvetica", 8.5)
        iban = footer.get("iban", "")
        # Partially mask IBAN as ES** XXXX-XXXX-XX-XXXXXXXX****
        c.drawString(bx + 65, by - 12, iban)
        by -= 14
        if invoice.due_date:
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(bx, by - 12, "VENCIMIENTOS:")
            c.setFont("Helvetica", 8.5)
            c.drawString(bx + 80, by - 12, invoice.due_date.strftime("%d/%m/%y"))
            by -= 14
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(bx, by - 12, "IMPORTES:")
            c.setFont("Helvetica", 8.5)
            c.drawString(bx + 65, by - 12, f"{invoice.total:,.2f}".replace(",", "."))

        # ── NOTES ────────────────────────────────────────────────────────────
        note_y = min(ty - 25, by - 25)
        if invoice.notes:
            note_y -= 5
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.black)
            c.drawString(30, note_y, invoice.notes[:120])
            note_y -= 12

        # ── LOPD FOOTER ───────────────────────────────────────────────────────
        lopd = (
            "Información Básica sobre Protección de Datos — "
            f"Responsable: {footer.get('legal_name') or footer.get('company_name', '')}. "
            "Finalidad: Gestión de Clientes. Legitimación: El propio interesado. "
            "Destinatarios: No se cederán a terceros, salvo obligación legal. "
            "Derechos: Tiene derecho a acceder, rectificar y suprimir los datos, así como otros derechos "
            "indicados en la información adicional, que puede solicitar enviando un correo a: "
            f"{footer.get('email', '')}. "
            "Información adicional: Puede solicitar información adicional y detallada sobre protección de "
            f"datos enviando un correo a {footer.get('email', '')}"
        )
        c.setFont("Helvetica", 5.5)
        c.setFillColor(colors.HexColor("#444444"))
        wrapped = textwrap.wrap(lopd, width=175)
        fy = 38
        for line in wrapped[:4]:
            c.drawCentredString(W / 2, fy, line)
            fy -= 8

        c.save()
        pdf_bytes = buffer.getvalue()
        filename = f"{invoice.invoice_number}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ProformaGeneratePDFView(BackofficeRequiredMixin, View):
    """
    Generate a PDF for a proforma invoice (FACTURA PROFORMA).
    Layout matches the Pre reference document.
    """

    def post(self, request, pk):
        import io
        import os
        from django.conf import settings
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from apps.core.instance import get_branding, get_profile

        proforma = get_object_or_404(
            ProformaInvoice.objects.select_related("customer__user")
            .prefetch_related("items__tax_rate"),
            pk=pk,
        )

        branding = get_branding()
        footer = branding.get("footer", {})

        W, H = A4  # 595 x 842 pt
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setLineWidth(0.5)

        instance_id = get_profile().get("instance_id", "")
        logo_path = os.path.join(
            settings.BASE_DIR, "instances", instance_id,
            "static", instance_id, "logo_blanco.png",
        )

        # ── HEADER ────────────────────────────────────────────────────────────
        # Left: logo
        if os.path.isfile(logo_path):
            try:
                c.drawImage(logo_path, 30, H - 80, width=130, height=52,
                            preserveAspectRatio=True, mask="auto")
            except Exception:
                c.setFont("Helvetica-Bold", 14)
                c.drawString(30, H - 60, footer.get("company_name", ""))
        else:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(30, H - 60, footer.get("company_name", ""))

        # Right: title
        c.setFont("Helvetica-Bold", 20)
        c.drawRightString(W - 30, H - 52, "FACTURA PROFORMA")

        # ── SEPARATOR ────────────────────────────────────────────────────────
        c.setStrokeColor(colors.black)
        c.line(30, H - 88, W - 30, H - 88)

        # ── EMISOR BLOCK (left) ───────────────────────────────────────────────
        y = H - 104
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.black)
        c.drawString(30, y, footer.get("legal_name") or footer.get("company_name", ""))
        y -= 13
        c.setFont("Helvetica", 9)
        if footer.get("address"):
            c.drawString(30, y, footer["address"])
            y -= 13
        if footer.get("zip") and footer.get("city"):
            c.drawString(30, y, f"{footer['zip']}  {footer['city'].upper()}")
            y -= 13
        if footer.get("province"):
            c.drawString(30, y, footer["province"].upper())
            y -= 13
        if footer.get("tax_id"):
            c.drawString(30, y, f"C.I.F.:  {footer['tax_id']}")
            y -= 13
        if footer.get("phone"):
            c.drawString(30, y, f"Telf./Fax:  {footer['phone']}")
            y -= 13
        if footer.get("email"):
            c.drawString(30, y, footer["email"])
            y -= 13
        emisor_bottom = y

        # ── MINI REFERENCE TABLE (left, below emisor) ─────────────────────────
        mini_y = emisor_bottom - 8
        mini_h = 34  # header(17) + value(17)
        mini_w = 242
        col_widths = [80, 80, 82]
        col_labels = ["FRA PROFORMA", "FECHA", "Cod.Cliente"]
        col_values = [
            proforma.proforma_number,
            proforma.issued_at.strftime("%d/%m/%Y"),
            proforma.customer_code_snapshot,
        ]
        # Header row
        c.setFillColor(colors.black)
        c.rect(30, mini_y - mini_h, mini_w, mini_h, stroke=1, fill=0)
        hdr_y = mini_y - 12
        val_y = mini_y - 28
        cx = 30
        for i, (lbl, val) in enumerate(zip(col_labels, col_values)):
            # vertical separator
            if i > 0:
                c.line(cx, mini_y, cx, mini_y - mini_h)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(cx + col_widths[i] / 2, hdr_y, lbl)
            c.setFont("Helvetica", 9)
            c.drawCentredString(cx + col_widths[i] / 2, val_y, str(val))
            cx += col_widths[i]
        # Horizontal divider between header and values
        c.line(30, mini_y - 17, 30 + mini_w, mini_y - 17)
        mini_table_bottom = mini_y - mini_h

        # ── DESTINATARIO BOX (right) ──────────────────────────────────────────
        dest_x = 290
        dest_top = H - 100
        dest_bottom = mini_table_bottom - 2
        dest_h = dest_top - dest_bottom
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.black)
        c.rect(dest_x, dest_bottom, W - 30 - dest_x, dest_h, stroke=1, fill=0)

        addr_lines = [l.strip() for l in proforma.billing_address_snapshot.splitlines() if l.strip()]
        dy = dest_top - 14
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.black)
        c.drawString(dest_x + 5, dy, proforma.billing_name_snapshot or str(proforma.customer))
        dy -= 13
        c.setFont("Helvetica", 9)
        for al in addr_lines[:2]:
            c.drawString(dest_x + 5, dy, al)
            dy -= 13
        if proforma.billing_province_snapshot:
            c.drawString(dest_x + 5, dy, proforma.billing_province_snapshot.upper())
            dy -= 13
        # TELF + CIF on same line
        telf_str = f"TELF: {proforma.customer_phone_snapshot}" if proforma.customer_phone_snapshot else ""
        cif_str = f"CIF.:  {proforma.tax_id_snapshot}" if proforma.tax_id_snapshot else ""
        c.setFont("Helvetica-Bold", 8.5)
        if telf_str:
            c.drawString(dest_x + 5, dy, telf_str)
        if cif_str:
            c.drawString(dest_x + 5 + 110, dy, cif_str)

        # ── LINE ITEMS TABLE ──────────────────────────────────────────────────
        # COD(55) | DESCRIPCION(195) | TONO(55) | UDS(65) | PVP(65) | IMPORTE(100)
        P_COL_X = [30, 85, 280, 335, 400, 465]
        P_COL_W = [55, 195, 55, 65, 65, 100]
        P_HEADERS = ["COD.", "DESCRIPCION", "TONO", "UDS.", "PVP", "IMPORTE"]

        table_top = mini_table_bottom - 12

        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        c.rect(30, table_top - 17, W - 60, 17, stroke=1, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        for i, h in enumerate(P_HEADERS):
            if i < 2:
                c.drawString(P_COL_X[i] + 3, table_top - 12, h)
            else:
                c.drawCentredString(P_COL_X[i] + P_COL_W[i] / 2, table_top - 12, h)

        y = table_top - 17
        c.setFillColor(colors.black)
        row = 0
        for item in proforma.items.all():
            if row % 2 == 0:
                c.setFillColor(colors.HexColor("#f3f4f6"))
                c.rect(30, y - 15, W - 60, 15, stroke=0, fill=1)
                c.setFillColor(colors.black)
            c.setFont("Helvetica", 8.5)
            c.drawString(P_COL_X[0] + 3, y - 10, str(item.product_code)[:8])
            desc = str(item.description)
            c.drawString(P_COL_X[1] + 3, y - 10, desc[:32] + ("..." if len(desc) > 32 else ""))
            c.drawCentredString(P_COL_X[2] + P_COL_W[2] / 2, y - 10, str(item.tono)[:8])
            c.drawCentredString(P_COL_X[3] + P_COL_W[3] / 2, y - 10,
                                f"{item.quantity:,.2f}".replace(",", "."))
            c.drawCentredString(P_COL_X[4] + P_COL_W[4] / 2, y - 10,
                                f"{item.unit_price:,.2f}".replace(",", "."))
            c.drawRightString(P_COL_X[5] + P_COL_W[5] - 3, y - 10,
                              f"{item.line_total:,.2f}".replace(",", "."))
            y -= 15
            row += 1

        # Draw bottom border of items area
        c.setStrokeColor(colors.black)
        c.line(30, y, W - 30, y)

        # ── TOTALS ROW (horizontal 4-column table) ────────────────────────────
        tot_y = y - 2
        tot_row_h = 36  # header(18) + value(18)
        tot_col_w = (W - 60) / 4  # ~133.75 each
        tot_labels = ["IMP. BRUTO", "BASE IMPONIBLE", "IMPORTE IVA", "TOTAL EUR."]
        tot_values = [
            f"{proforma.subtotal:,.2f}".replace(",", "."),
            f"{proforma.subtotal:,.2f}".replace(",", "."),
            f"{proforma.tax_amount:,.2f}".replace(",", "."),
            f"{proforma.total:,.2f}".replace(",", "."),
        ]
        c.setFillColor(colors.black)
        c.rect(30, tot_y - tot_row_h, W - 60, tot_row_h, stroke=1, fill=0)
        c.line(30, tot_y - 18, W - 30, tot_y - 18)  # row divider
        for i in range(4):
            cx = 30 + i * tot_col_w
            if i > 0:
                c.line(cx, tot_y, cx, tot_y - tot_row_h)  # vertical divider
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(cx + tot_col_w / 2, tot_y - 13, tot_labels[i])
            c.setFont("Helvetica", 9)
            if i == 3:
                c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(cx + tot_col_w / 2, tot_y - 30, tot_values[i])

        # ── PAYMENT FOOTER ────────────────────────────────────────────────────
        pay_y = tot_y - tot_row_h - 15
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.black)
        pay_method = proforma.payment_method or "TRANSF."
        iban = footer.get("iban", "")
        c.drawString(30, pay_y, f"Forma de Pago:   {pay_method}  {iban}   CCC:")

        c.save()
        pdf_bytes = buffer.getvalue()
        filename = f"Proforma_{proforma.proforma_number}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


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
        ctx["category_list"] = ProductCategory.objects.filter(is_active=True).order_by(
            "name"
        )
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
        return ProductCategory.objects.select_related("parent").order_by(
            f"{prefix}{order_field}", "name"
        )

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
        year = invoice.issued_at.year if invoice.issued_at else timezone.now().year
        invoice.number = num
        invoice.invoice_number = f"{series.prefix}-{year}-{num:04d}"
        # Billing snapshots from customer
        customer = form.cleaned_data["customer"]
        invoice.billing_name_snapshot = customer.billing_name
        invoice.tax_id_snapshot = customer.tax_id or ""
        invoice.customer_code_snapshot = customer.customer_code
        invoice.customer_phone_snapshot = customer.phone
        invoice.status = "draft"
        invoice.save()
        messages.success(self.request, f"Factura {invoice.invoice_number} creada.")
        return redirect("backoffice:invoice_detail", pk=invoice.pk)


# ── Proforma invoices ─────────────────────────────────────────────────────────


class ProformaListView(BackofficeRequiredMixin, ListView):
    template_name = "backoffice/proformas/list.html"
    context_object_name = "proformas"
    paginate_by = 25

    def get_queryset(self):
        qs = ProformaInvoice.objects.select_related("customer__user").order_by("-issued_at")
        status = self.request.GET.get("status")
        q = self.request.GET.get("q", "").strip()
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(proforma_number__icontains=q) | qs.filter(
                customer__user__email__icontains=q
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = ProformaInvoice.STATUS_CHOICES
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class ProformaDetailView(BackofficeRequiredMixin, DetailView):
    template_name = "backoffice/proformas/detail.html"
    model = ProformaInvoice
    context_object_name = "proforma"

    def get_queryset(self):
        return ProformaInvoice.objects.select_related("customer__user").prefetch_related(
            "items__tax_rate"
        )


class ProformaCreateView(BackofficeRequiredMixin, View):
    template_name = "backoffice/proformas/create.html"

    def get(self, request):
        from django.shortcuts import render
        return render(request, self.template_name, {"customers": Customer.objects.all()})

    def post(self, request):
        from django.utils import timezone as tz

        customer_id = request.POST.get("customer")
        customer = get_object_or_404(Customer, pk=customer_id)
        issued_at = tz.now()
        year = issued_at.year
        num, proforma_number = ProformaInvoice.create_number(year)

        proforma = ProformaInvoice.objects.create(
            customer=customer,
            number=num,
            proforma_number=proforma_number,
            issued_at=issued_at,
            status="draft",
            billing_name_snapshot=customer.billing_name,
            tax_id_snapshot=customer.tax_id or "",
            customer_code_snapshot=customer.customer_code,
            customer_phone_snapshot=customer.phone,
            payment_method=request.POST.get("payment_method", ""),
            notes=request.POST.get("notes", ""),
        )
        messages.success(request, f"Proforma {proforma.proforma_number} creada.")
        return redirect("backoffice:proforma_detail", pk=proforma.pk)


class ProformaUpdateView(BackofficeRequiredMixin, UpdateView):
    template_name = "backoffice/proformas/edit.html"
    model = ProformaInvoice
    fields = [
        "status",
        "billing_name_snapshot",
        "tax_id_snapshot",
        "billing_address_snapshot",
        "customer_code_snapshot",
        "customer_phone_snapshot",
        "billing_province_snapshot",
        "payment_method",
        "subtotal",
        "tax_amount",
        "total",
        "notes",
    ]

    def get_success_url(self):
        return reverse_lazy("backoffice:proforma_detail", kwargs={"pk": self.object.pk})


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
        messages.success(self.request, f"Pedido {order.order_number} creado.")
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
        (
            "Sustituye el suelo por un material cerámico basado en la imagen de azulejo "
            "proporcionada como referencia. Ajusta el patrón del suelo a la perspectiva real "
            "(escala, orientación y repetición correctas). "
            "Mantén realismo en juntas, textura y acabado (mate/brillo). "
        )
        if has_tile
        else ("No modifiques el suelo. ")
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
                {
                    "error": "La librería openai no está instalada. Ejecuta: pip install openai"
                },
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
        tile_file = self._resolve_tile_file(request)
        wall_color = request.POST.get("wall_color", "#FFFFFF").strip()

        # ── Validaciones ──────────────────────────────────────────────────────
        if not room_file:
            return JsonResponse(
                {"error": "Debes subir una imagen de la habitación."}, status=400
            )

        if not (wall_color.startswith("#") and len(wall_color) in (4, 7)):
            return JsonResponse(
                {"error": "Color de pared no válido. Usa formato #RRGGBB."}, status=400
            )

        # Only validate content_type/size for directly uploaded files
        for label, f in [("habitación", room_file)]:
            if f is None:
                continue
            if (
                getattr(f, "content_type", None)
                and f.content_type not in self._ALLOWED_TYPES
            ):
                return JsonResponse(
                    {
                        "error": f"Formato de imagen de {label} no válido. Usa PNG, JPEG o WebP."
                    },
                    status=400,
                )
            if getattr(f, "size", 0) > self._MAX_SIZE:
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
                (name, io.BytesIO(data), mime) for name, data, mime in images_param
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
            return JsonResponse(
                {"error": f"Error de la API de OpenAI: {exc}"}, status=502
            )
        except Exception:
            logger.exception("Error inesperado en VisualizaObraView")
            return JsonResponse({"error": "Error interno del servidor."}, status=500)

    def _resolve_tile_file(self, request):
        """Returns the tile file object or None. Prefers uploaded file; falls back to variant."""
        tile_file = request.FILES.get("tile_image")
        if tile_file:
            return tile_file
        variant_pk = request.POST.get("tile_variant_pk", "").strip()
        if not variant_pk:
            return None
        try:
            variant = ProductVariant.objects.get(pk=int(variant_pk))
            if variant.image:
                return variant.image.open("rb")
        except (ProductVariant.DoesNotExist, ValueError, OSError):
            pass
        return None


class ProductImagePickerView(BackofficeRequiredMixin, View):
    """AJAX endpoint: returns catalog products (with images) as JSON for the VTO picker."""

    def get(self, request):
        q = request.GET.get("q", "").strip()
        category_pk = request.GET.get("categoria", "").strip()
        brand_pk = request.GET.get("marca", "").strip()

        qs = (
            Product.objects.filter(is_active=True)
            .select_related("category", "brand")
            .prefetch_related("variants")
        )
        if q:
            qs = qs.filter(name__icontains=q)
        if category_pk:
            qs = qs.filter(category_id=category_pk)
        if brand_pk:
            qs = qs.filter(brand_id=brand_pk)

        results = []
        for product in qs[:60]:
            for variant in product.variants.filter(is_active=True):
                if not variant.image:
                    continue
                results.append(
                    {
                        "variant_pk": variant.pk,
                        "product_name": product.name,
                        "variant_name": variant.name or "",
                        "sku": variant.sku,
                        "image_url": request.build_absolute_uri(variant.image.url),
                        "category": product.category.name if product.category else "",
                        "brand": product.brand.name if product.brand else "",
                    }
                )

        categories = list(
            ProductCategory.objects.filter(is_active=True)
            .values("pk", "name")
            .order_by("name")
        )
        brands = list(
            ProductBrand.objects.filter(is_active=True)
            .values("pk", "name")
            .order_by("name")
        )
        return JsonResponse(
            {"results": results, "categories": categories, "brands": brands}
        )
