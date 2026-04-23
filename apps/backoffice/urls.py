from django.urls import path
from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("pedidos/", views.OrderListView.as_view(), name="order_list"),
    path("pedidos/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("clientes/", views.CustomerListView.as_view(), name="customer_list"),
    path("clientes/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("facturas/", views.InvoiceListView.as_view(), name="invoice_list"),
    path("facturas/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice_detail"),
    path("catalogo/", views.CatalogListView.as_view(), name="catalog_list"),
]
