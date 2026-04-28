"""
URL configuration for Huan Commerce Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from apps.core.views import IndexView, CookiePolicyView

urlpatterns = [
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/helvagres_demo/icono.png", permanent=False),
    ),
    path("", IndexView.as_view(), name="index"),
    path("politica-de-cookies/", CookiePolicyView.as_view(), name="cookie_policy"),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.catalog.catalog_urls")),
    path("", include("apps.cart.urls")),
    path("", include("apps.services.urls")),
    path("admin/", admin.site.urls),
    path("panel/", include("apps.backoffice.urls")),
    path("api/", include("apps.catalog.urls")),
    path("api/", include("apps.customers.urls")),
    path("api/", include("apps.orders.urls")),
    path("api/", include("apps.invoicing.urls")),
]

if settings.DEBUG:
    from django.contrib.staticfiles import views as staticfiles_views
    from django.urls import re_path

    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", staticfiles_views.serve, {"insecure": True}),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
