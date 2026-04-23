from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("mi-cuenta/", views.CustomerPortalView.as_view(), name="portal"),
    path("mi-cuenta/pedido/nuevo/", views.OrderRequestView.as_view(), name="order_request"),
]
