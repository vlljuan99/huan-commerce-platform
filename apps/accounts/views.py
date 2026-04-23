"""
Accounts views: login, logout, customer portal, order request.
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from apps.orders.models import Order


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return self._redirect_after_login(request.user)
        return render(request, self.template_name, {"form": AuthenticationForm()})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return self._redirect_after_login(form.get_user())
        return render(request, self.template_name, {"form": form})

    def _redirect_after_login(self, user):
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
        return render(request, self.template_name, {
            "customer": customer,
            "orders": orders,
        })


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

        # Generate order number: ORD-YYYY-NNNN
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

        full_notes = f"Ref. cliente: {reference}\n\n{notes}".strip() if reference else notes

        Order.objects.create(
            customer=customer,
            order_number=f"ORD-{year}-{n:04d}",
            status="pending",
            notes=full_notes,
        )
        return redirect("accounts:portal")
