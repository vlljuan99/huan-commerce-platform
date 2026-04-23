"""
WSGI config for Huan Commerce Platform.

En producción, definir DJANGO_SETTINGS_MODULE o HUAN_INSTANCE en el entorno
del servidor / proceso gunicorn antes de arrancar.
"""

import os

from django.core.wsgi import get_wsgi_application


def _resolve_settings_module() -> str:
    if os.environ.get('DJANGO_SETTINGS_MODULE'):
        return os.environ['DJANGO_SETTINGS_MODULE']
    instance = os.environ.get('HUAN_INSTANCE')
    if instance:
        return f'instances.{instance}.settings'
    return 'config.settings.base'


os.environ.setdefault('DJANGO_SETTINGS_MODULE', _resolve_settings_module())

application = get_wsgi_application()
