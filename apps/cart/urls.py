"""
URLs for Cart app.
"""

from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("carrito/", views.CartDetailView.as_view(), name="detail"),
    path("carrito/añadir/<int:variant_pk>/", views.CartAddView.as_view(), name="add"),
    path("carrito/añadir/servicio/<int:service_pk>/", views.CartAddServiceView.as_view(), name="add_service"),
    path("carrito/eliminar/<int:item_pk>/", views.CartRemoveView.as_view(), name="remove"),
    path("carrito/actualizar/<int:item_pk>/", views.CartUpdateView.as_view(), name="update"),
]
