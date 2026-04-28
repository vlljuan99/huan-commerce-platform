"""
Accounts views: login, logout, customer portal, order request, checkout.
"""

from decimal import Decimal

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from apps.cart.views import get_or_create_cart, merge_session_cart
from apps.orders.models import Order, OrderLineItem


def _next_order_number():
    """Generate the next ORD-YYYY-NNNN order number atomically."""
    year = timezone.now().year
    prefix = f"ORD-{year}-"
    last = (
        Order.objects.filter(order_number__startswith=prefix)
        .order_by("-order_number")
        .first()
    )
    try:
        n = int(last.order_number[len(prefix) :]) + 1 if last else 1
    except (ValueError, IndexError):
        n = 1
    return f"{prefix}{n:04d}"


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return self._redirect_after_login(request)
        return render(request, self.template_name, {"form": AuthenticationForm()})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            old_session_key = request.session.session_key
            user = form.get_user()
            login(request, user)
            merge_session_cart(old_session_key, user)
            return self._redirect_after_login(request)
        return render(request, self.template_name, {"form": form})

    def _redirect_after_login(self, request):
        next_url = request.GET.get("next") or request.POST.get("next", "")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        user = request.user
        if user.is_superuser or user.role in ("admin", "commercial"):
            return redirect("/panel/")
        return redirect("accounts:portal")


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("index")


class CustomerPortalView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    template_name = "accounts/portal.html"

    def get(self, request):
        customer = getattr(request.user, "customer_profile", None)
        orders = (
            Order.objects.filter(customer=customer).order_by("-created_at")
            if customer
            else []
        )
        return render(
            request,
            self.template_name,
            {
                "customer": customer,
                "orders": orders,
            },
        )


class OrderRequestView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"
    template_name = "accounts/order_request.html"

    def _get_customer(self, request):
        return getattr(request.user, "customer_profile", None)

    def get(self, request):
        customer = self._get_customer(request)
        if not customer:
            return redirect("accounts:portal")
        return render(request, self.template_name, {"customer": customer})

    def post(self, request):
        customer = self._get_customer(request)
        if not customer:
            return redirect("accounts:portal")

        notes = request.POST.get("notes", "").strip()
        reference = request.POST.get("reference", "").strip()
        full_notes = (
            f"Ref. cliente: {reference}\n\n{notes}".strip() if reference else notes
        )

        with transaction.atomic():
            Order.objects.create(
                customer=customer,
                order_number=_next_order_number(),
                status="pending",
                notes=full_notes,
            )
        return redirect("accounts:portal")


class CheckoutView(LoginRequiredMixin, View):
    login_url = "/accounts/login/?next=/accounts/mi-cuenta/checkout/"
    template_name = "accounts/checkout.html"

    def _get_customer(self, request):
        return getattr(request.user, "customer_profile", None)

    def get(self, request):
        customer = self._get_customer(request)
        cart = get_or_create_cart(request)
        items = cart.items.select_related(
            "variant__product__category", "variant__product__brand"
        ).order_by("added_at")
        return render(
            request,
            self.template_name,
            {
                "customer": customer,
                "cart": cart,
                "items": items,
                "total": cart.get_total(),
            },
        )

    def post(self, request):
        customer = self._get_customer(request)
        if not customer:
            return redirect("accounts:portal")

        cart = get_or_create_cart(request)
        items = cart.items.select_related("variant__product").order_by("added_at")
        if not items.exists():
            return redirect("cart:detail")

        notes = request.POST.get("notes", "").strip()

        subtotal = cart.get_total()
        with transaction.atomic():
            order = Order.objects.create(
                customer=customer,
                order_number=_next_order_number(),
                status="pending",
                notes=notes,
                subtotal=subtotal,
                total=subtotal,
            )
            for item in items:
                unit_price = item.display_unit_price
                line_total = Decimal(item.quantity) * unit_price
                OrderLineItem.objects.create(
                    order=order,
                    variant=item.variant,
                    product_name=item.display_name,
                    sku=item.display_sku,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            cart.items.all().delete()

        return render(request, "accounts/checkout_done.html", {"order": order})
