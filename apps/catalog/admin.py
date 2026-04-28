"""
Admin registrations for Catalog app.
"""

from django.contrib import admin
from .models import Product, ProductVariant, ProductCategory, ProductBrand, ProductImage


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = (
        "sku",
        "name",
        "price_no_tax",
        "stock_quantity",
        "image",
        "is_active",
        "display_order",
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("variant", "image", "alt_text", "display_order")


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "display_order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("display_order", "name")


@admin.register(ProductBrand)
class ProductBrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "category",
        "brand",
        "sku_base",
        "is_featured",
        "is_active",
    )
    list_filter = ("is_active", "is_featured", "category", "brand")
    search_fields = ("name", "slug", "sku_base")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "category",
                    "brand",
                    "sku_base",
                    "is_active",
                ),
            },
        ),
        (
            "Detalles",
            {
                "fields": ("unit_of_measure", "weight", "is_featured"),
            },
        ),
        (
            "SEO",
            {
                "fields": ("seo_title", "seo_description"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "product",
        "name",
        "price_no_tax",
        "stock_quantity",
        "is_active",
    )
    list_filter = ("is_active", "product__category")
    search_fields = ("sku", "name", "product__name")
    inlines = [ProductImageInline]
