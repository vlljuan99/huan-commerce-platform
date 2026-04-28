#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _resolve_settings_module() -> str:
    """
    Determina el módulo de settings en este orden:
      1. DJANGO_SETTINGS_MODULE ya definido en entorno → se respeta
      2. HUAN_INSTANCE definido → carga instances/<id>/settings.py
      3. Fallback → config.settings.base
    """
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return os.environ["DJANGO_SETTINGS_MODULE"]

    instance = os.environ.get("HUAN_INSTANCE")
    if instance:
        return f"instances.{instance}.settings"

    return "config.settings.base"


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", _resolve_settings_module())
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
