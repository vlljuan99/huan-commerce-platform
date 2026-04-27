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

    # Catalog — categories
    path("catalogo/categorias/", views.CategoryListView.as_view(), name="category_list"),
    path("catalogo/categorias/nueva/", views.CategoryCreateView.as_view(), name="category_create"),
    path("catalogo/categorias/<int:pk>/editar/", views.CategoryUpdateView.as_view(), name="category_edit"),

    # Catalog — brands
    path("catalogo/marcas/", views.BrandListView.as_view(), name="brand_list"),
    path("catalogo/marcas/nueva/", views.BrandCreateView.as_view(), name="brand_create"),
    path("catalogo/marcas/<int:pk>/editar/", views.BrandUpdateView.as_view(), name="brand_edit"),

    # Catalog PDFs
    path("catalogos-pdf/", views.CatalogPDFListView.as_view(), name="catalogpdf_list"),
    path("catalogos-pdf/nuevo/", views.CatalogPDFCreateView.as_view(), name="catalogpdf_create"),
    path("catalogos-pdf/<int:pk>/editar/", views.CatalogPDFUpdateView.as_view(), name="catalogpdf_edit"),
    path("catalogos-pdf/<int:pk>/eliminar/", views.CatalogPDFDeleteView.as_view(), name="catalogpdf_delete"),

    # Services
    path("servicios/", views.ServiceListView.as_view(), name="service_list"),
    path("servicios/nuevo/", views.ServiceCreateView.as_view(), name="service_create"),
    path("servicios/<int:pk>/editar/", views.ServiceUpdateView.as_view(), name="service_edit"),

    # Service categories
    path("servicios/categorias/", views.ServiceCategoryListView.as_view(), name="service_category_list"),
    path("servicios/categorias/nueva/", views.ServiceCategoryCreateView.as_view(), name="service_category_create"),
    path("servicios/categorias/<int:pk>/editar/", views.ServiceCategoryUpdateView.as_view(), name="service_category_edit"),

    # Companies
    path("empresas/", views.CompanyListView.as_view(), name="company_list"),
    path("empresas/nueva/", views.CompanyCreateView.as_view(), name="company_create"),
    path("empresas/<int:pk>/editar/", views.CompanyUpdateView.as_view(), name="company_edit"),

    # Visualiza tu Obra (IA)
    path("visualiza-tu-obra/", views.VisualizaObraView.as_view(), name="visualiza_obra"),
    path("visualiza-tu-obra/productos/", views.ProductImagePickerView.as_view(), name="product_image_picker"),
]
