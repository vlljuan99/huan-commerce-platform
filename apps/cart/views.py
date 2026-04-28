"""
Cart views: add, remove, update, detail.
"""

from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.cart.models import Cart, CartLineItem
from apps.catalog.models import ProductVariant
from apps.services.models import Service


def get_or_create_cart(request):
    """Get or create a cart for the current request (user or session-based)."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


def merge_session_cart(session_key, user):
    """
    After login, merge the anonymous session cart into the user's cart.
    Call this with the OLD session key, before Django's login() rotates it.
    """
    if not session_key:
        return
    try:
        session_cart = Cart.objects.filter(session_key=session_key, user=None).first()
        if not session_cart:
            return
        user_cart, _ = Cart.objects.get_or_create(user=user)
        for item in session_cart.items.all():
            user_item, created = CartLineItem.objects.get_or_create(
                cart=user_cart,
                variant=item.variant,
                defaults={"quantity": item.quantity},
            )
            if not created:
                user_item.quantity += item.quantity
                user_item.save(update_fields=["quantity"])
        session_cart.delete()
    except Exception:
        pass


class CartDetailView(View):
    def get(self, request):
        cart = get_or_create_cart(request)
        items = cart.items.select_related(
            "variant__product__category", "variant__product__brand"
        ).order_by("added_at")
        return render(
            request,
            "cart/cart.html",
            {
                "cart": cart,
                "items": items,
                "total": cart.get_total(),
            },
        )


class CartAddView(View):
    def post(self, request, variant_pk):
        variant = get_object_or_404(ProductVariant, pk=variant_pk)
        try:
            quantity = max(1, int(request.POST.get("quantity", 1)))
        except (ValueError, TypeError):
            quantity = 1
        cart = get_or_create_cart(request)
        item, created = CartLineItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        next_url = request.POST.get("next", "")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect("cart:detail")


class CartRemoveView(View):
    def post(self, request, item_pk):
        cart = get_or_create_cart(request)
        CartLineItem.objects.filter(pk=item_pk, cart=cart).delete()
        return redirect("cart:detail")


class CartAddServiceView(View):
    def post(self, request, service_pk):
        service = get_object_or_404(Service, pk=service_pk, is_active=True)
        try:
            quantity = max(1, int(request.POST.get("quantity", 1)))
        except (ValueError, TypeError):
            quantity = 1
        cart = get_or_create_cart(request)
        item, created = CartLineItem.objects.get_or_create(
            cart=cart,
            service=service,
            variant=None,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=["quantity"])
        next_url = request.POST.get("next", "")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect("cart:detail")


class CartUpdateView(View):
    def post(self, request, item_pk):
        cart = get_or_create_cart(request)
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (ValueError, TypeError):
            quantity = 1
        if quantity <= 0:
            CartLineItem.objects.filter(pk=item_pk, cart=cart).delete()
        else:
            CartLineItem.objects.filter(pk=item_pk, cart=cart).update(quantity=quantity)
        return redirect("cart:detail")
