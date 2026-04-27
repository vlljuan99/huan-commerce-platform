from django.contrib import admin
from .models import Company, ServiceCategory, Service


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "is_own", "is_active", "phone", "email"]
    list_filter = ["is_own", "is_active"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "display_order", "is_active"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "company", "price", "unit", "is_active", "is_featured"]
    list_filter = ["category", "company", "is_active", "is_featured"]
    prepopulated_fields = {"slug": ("name",)}
