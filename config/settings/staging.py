"""
config/settings/staging.py

Entorno de pre-producción / testing desplegado en Heroku.
Se activa con: DJANGO_SETTINGS_MODULE=config.settings.staging
"""
# ruff: noqa: F405

from config.settings.base import *  # noqa: F401, F403, F405

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*.herokuapp.com"])

# HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files → Azure Blob Storage via django-storages
INSTALLED_APPS += ["storages"]  # noqa: F405

AZURE_ACCOUNT_NAME = env("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_ACCOUNT_KEY = env("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_STATIC_CONTAINER = env("AZURE_STATIC_CONTAINER", default="static")
AZURE_CONTAINER = AZURE_STATIC_CONTAINER  # django-storages reads AZURE_CONTAINER

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
    },
}
AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"
STATIC_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{AZURE_STATIC_CONTAINER}/"

# Email real (configurable vía vars de entorno en Heroku)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="staging@huan.com")

# Cache con Redis (Heroku Redis addon)
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# Celery con Redis
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# CORS — ajustar al dominio de staging del frontend si lo hay
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
