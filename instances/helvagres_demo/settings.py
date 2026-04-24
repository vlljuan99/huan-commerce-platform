"""
Settings for instance: helvagres_demo

Extiende config.settings.base y aplica overrides específicos de esta instancia.
Selección mediante variable de entorno:
    DJANGO_SETTINGS_MODULE=instances.helvagres_demo.settings

O usando HUAN_INSTANCE=helvagres_demo con manage.py / wsgi.py
"""

from config.settings.base import *  # noqa: F401, F403
from pathlib import Path
import os

# Directorio raíz de esta instancia
INSTANCE_DIR = Path(__file__).resolve().parent
INSTANCE_ID = 'helvagres_demo'

# Cargar .env de la instancia si existe (sobrescribe el global)
if os.path.isfile(INSTANCE_DIR / '.env'):
    import environ
    _env = environ.Env()
    environ.Env.read_env(str(INSTANCE_DIR / '.env'))

# ── Base de datos (SQLite dedicada por instancia en dev) ──────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / f'db_{INSTANCE_ID}.sqlite3',  # noqa: F405
    }
}

# ── Localización de instancia ─────────────────────────────────────────────────
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'Europe/Madrid'

# ── Templates: el directorio de instancia tiene prioridad sobre el global ─────
# Los templates de instances/helvagres_demo/templates/ sobreescriben los base.
TEMPLATES[0]['DIRS'] = [  # noqa: F405
    INSTANCE_DIR / 'templates',   # overrides específicos de instancia (primero)
    BASE_DIR / 'templates',       # noqa: F405  # templates globales del proyecto
]

# ── Branding & features: cargados por el loader en apps.core.instance ─────────
# INSTANCE_ID es la clave que usa apps.core.instance para encontrar los JSON.
INSTANCE_DIR_STR = str(INSTANCE_DIR)

# ── Overrides de entorno local (ignorado en producción) ───────────────────────
try:
    from config.settings.local import *  # noqa: F401, F403
except ImportError:
    pass

# ── Ficheros estáticos específicos de instancia ───────────────────────────────
# Redefinido después de local.py para que no sea sobrescrito por base.py.
STATICFILES_DIRS = [
    INSTANCE_DIR / 'static',  # primero: assets de la instancia (con namespace <id>/)
    BASE_DIR / 'static',       # noqa: F405  # después: assets globales
]
