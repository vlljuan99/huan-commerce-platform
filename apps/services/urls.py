from django.urls import path
from . import views

app_name = "services"

urlpatterns = [
    path("servicios/", views.ServiceListView.as_view(), name="service_list"),
    path(
        "servicios/<slug:slug>/",
        views.ServiceDetailView.as_view(),
        name="service_detail",
    ),
]
