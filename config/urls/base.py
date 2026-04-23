"""
URL configuration for Huan Commerce Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import IndexView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('catalogo/', include('apps.catalog.catalog_urls')),
    path('admin/', admin.site.urls),
    path('api/', include('apps.catalog.urls')),
    path('api/', include('apps.customers.urls')),
    path('api/', include('apps.orders.urls')),
    path('api/', include('apps.invoicing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
