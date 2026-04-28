"""
config/settings/local.py

Settings de entorno LOCAL (developer machine).
Extiende base.py con overrides cómodos para desarrollo.

Uso:
    DJANGO_SETTINGS_MODULE=config.settings.local python manage.py runserver

Para desarrollo con instancia específica, preferir:
    HUAN_INSTANCE=helvagres_demo python manage.py runserver
(que carga instances/<id>/settings.py que ya extiende base)
"""

from config.settings.base import *  # noqa: F401, F403

DEBUG = True

# Todas las IPs locales permitidas
ALLOWED_HOSTS = ["*"]

# Panel de debug (instalar django-debug-toolbar si hace falta)
# INSTALLED_APPS += ['debug_toolbar']

# Email en consola
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Caché en memoria (sin Redis en local)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
