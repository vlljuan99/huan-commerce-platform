"""
apps/core/instance.py

Loader de configuración por instancia.

Lee branding.json, features.json y profile.json desde el directorio
de la instancia activa y los pone disponibles como dicts Python.

La instancia activa se determina en este orden de prioridad:
  1. Variable de entorno HUAN_INSTANCE
  2. Setting INSTANCE_ID en Django settings
  3. Fallback: 'default' (usa config/settings/base.py directamente)

Uso:
    from apps.core.instance import get_branding, get_features, get_profile
    from apps.core.instance import is_feature_enabled
"""

import json
import logging
import os
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

# ─── Ruta base del proyecto ───────────────────────────────────────────────────
BASE_DIR: Path = getattr(settings, 'BASE_DIR', Path(__file__).resolve().parent.parent.parent)

# ─── Caché simple en memoria (invalidada al recargar el módulo) ───────────────
# Usamos un dict mutable en lugar de lru_cache para poder invalidar manualmente
# y para que el auto-reloader de Django pueda limpiarla al detectar cambios.
_cache: dict = {}


def _get_instance_id() -> str:
    """Determina el ID de instancia activo."""
    return (
        os.environ.get('HUAN_INSTANCE')
        or getattr(settings, 'INSTANCE_ID', None)
        or 'default'
    )


def _get_instance_dir(instance_id: str) -> Path | None:
    """Devuelve el Path al directorio de la instancia, o None si no existe."""
    path = BASE_DIR / 'instances' / instance_id
    if path.is_dir():
        return path
    logger.warning("Instance directory not found: %s", path)
    return None


def _load_json(path: Path, filename: str) -> dict:
    """Carga un fichero JSON desde el directorio de instancia con fallback gracioso."""
    file = path / filename
    if not file.is_file():
        logger.debug("Instance file not found, skipping: %s", file)
        return {}
    try:
        with open(file, encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load %s: %s", file, exc)
        return {}


def _load_instance_config() -> dict:
    """
    Carga toda la configuración de la instancia activa.
    En producción el resultado se guarda en _cache; en DEBUG se recarga
    en cada proceso (el reloader lanza un proceso nuevo por cada cambio).
    """
    if not settings.DEBUG and 'config' in _cache:
        return _cache['config']

    instance_id = _get_instance_id()
    instance_dir = _get_instance_dir(instance_id)

    if instance_dir is None:
        config = {
            'id': instance_id,
            'dir': None,
            'branding': _branding_from_settings(),
            'features': _features_from_settings(),
            'profile': {},
        }
    else:
        raw_branding = _load_json(instance_dir, 'branding.json')
        raw_features = _load_json(instance_dir, 'features.json')
        raw_profile  = _load_json(instance_dir, 'profile.json')

        # Merge: base.py actúa como defaults, instance JSON sobreescribe
        config = {
            'id': instance_id,
            'dir': instance_dir,
            'branding': {**_branding_from_settings(), **raw_branding},
            'features': {**_features_from_settings(), **raw_features},
            'profile': raw_profile,
        }
        logger.info("Loaded instance config: %s", instance_id)

    _cache['config'] = config
    return config


def _branding_from_settings() -> dict:
    return dict(getattr(settings, 'BRANDING', {}))


def _features_from_settings() -> dict:
    return dict(getattr(settings, 'FEATURES', {}))


def invalidate_cache() -> None:
    """Invalida la caché del loader (útil en tests y en signals de recarga)."""
    _cache.clear()


# ─── API pública del módulo ───────────────────────────────────────────────────

def get_instance_id() -> str:
    return _load_instance_config()['id']


def get_branding() -> dict:
    return _load_instance_config()['branding']


def get_features() -> dict:
    return _load_instance_config()['features']


def get_profile() -> dict:
    return _load_instance_config()['profile']


def is_feature_enabled(flag: str) -> bool:
    """Comprueba si una feature flag está activa. Devuelve False si no existe."""
    return bool(get_features().get(flag, False))
