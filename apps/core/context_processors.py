"""
Template context processors for Huan Commerce Platform.

Exponen al contexto de todos los templates:
  - branding   → dict completo de branding de la instancia activa
  - features   → dict de feature flags de la instancia activa
  - instance   → id de instancia + profile
  - cart_count → número de ítems en el carrito del usuario actual
"""

from apps.core.instance import get_branding, get_features, get_instance_id, get_profile


def branding(request):
    """Expone el branding completo de la instancia al template."""
    return {'branding': get_branding()}


def features(request):
    """Expone las feature flags de la instancia al template."""
    return {'features': get_features()}


def instance(request):
    """Expone el id y perfil de la instancia activa al template."""
    return {
        'instance_id': get_instance_id(),
        'instance_profile': get_profile(),
    }


def cart_count(request):
    """Expone el número de ítems en el carrito al template."""
    count = 0
    try:
        from apps.cart.models import Cart
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            cart = Cart.objects.filter(session_key=session_key).first() if session_key else None
        if cart:
            count = cart.items.count()
    except Exception:
        pass
    return {'cart_count': count}
