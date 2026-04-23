from django.urls import path
from . import views

app_name = "backoffice"

urlpatterns = [
    # Dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),

    # Orders
    path("pedidos/", views.OrderListView.as_view(), name="order_list"),
    path("pedidos/nuevo/", views.OrderCreateView.as_view(), name="order_create"),
    path("pedidos/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("pedidos/<int:pk>/editar/", views.OrderUpdateView.as_view(), name="order_edit"),

    # Customers
    path("clientes/", views.CustomerListView.as_view(), name="customer_list"),
    path("clientes/nuevo/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("clientes/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("clientes/<int:pk>/editar/", views.CustomerUpdateView.as_view(), name="customer_edit"),
    path("clientes/<int:customer_pk>/direccion/nueva/", views.CustomerAddressCreateView.as_view(), name="customer_address_create"),
    path("direcciones/<int:pk>/editar/", views.CustomerAddressUpdateView.as_view(), name="address_edit"),

    # Invoices
    path("facturas/", views.InvoiceListView.as_view(), name="invoice_list"),
    path("facturas/nueva/", views.InvoiceCreateView.as_view(), name="invoice_create"),
    path("facturas/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice_detail"),
    path("facturas/<int:pk>/editar/", views.InvoiceUpdateView.as_view(), name="invoice_edit"),

    # Catalog — products
    path("catalogo/", views.CatalogListView.as_view(), name="catalog_list"),
    path("catalogo/nuevo/", views.ProductCreateView.as_view(), name="product_create"),
    path("catalogo/<int:pk>/editar/", views.ProductUpdateView.as_view(), name="product_edit"),

    # Catalog — variants
    path("catalogo/<int:product_pk>/variante/nueva/", views.ProductVariantCreateView.as_view(), name="variant_create"),
    path("variantes/<int:pk>/editar/", views.ProductVariantUpdateView.as_view(), name="variant_edit"),
]
