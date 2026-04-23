"""
Template context processors for Huan Commerce Platform.

Exponen al contexto de todos los templates:
  - branding   → dict completo de branding de la instancia activa
  - features   → dict de feature flags de la instancia activa
  - instance   → id de instancia + profile
  - cart_count → número de ítems en el carrito del usuario actual

Prioridad de branding: BrandingSettings (BD) > branding.json > defaults internos
"""

from apps.core.instance import get_branding, get_features, get_instance_id, get_profile


def _get_db_branding(instance_id: str) -> dict:
    """
    Lee el BrandingSettings de la BD para la instancia activa.
    Devuelve dict vacío si no existe o si la BD no está disponible.
    """
    try:
        from apps.core.models import BrandingSettings
        obj = BrandingSettings.objects.filter(instance_id=instance_id).first()
        return obj.as_dict() if obj else {}
    except Exception:
        # La BD puede no estar disponible durante migraciones o tests
        return {}


def _merge_branding(json_branding: dict, db_branding: dict) -> dict:
    """
    Fusiona branding.json con los valores de BD.
    BD tiene prioridad; los subdicts (como 'colors') se fusionan campo a campo.
    """
    merged = dict(json_branding)
    for key, value in db_branding.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def branding(request):
    """Expone el branding completo de la instancia al template."""
    instance_id = get_instance_id()
    json_branding = get_branding()
    db_branding = _get_db_branding(instance_id)
    return {'branding': _merge_branding(json_branding, db_branding)}


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
