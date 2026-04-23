"""
Admin registrations for Orders app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderLineItem


class OrderLineItemInline(admin.TabularInline):
    model = OrderLineItem
    extra = 1
    fields = (
        'variant', 'product_name', 'sku',
        'quantity', 'unit_price', 'tax_rate_pct', 'tax_amount', 'line_total',
    )
    readonly_fields = ('tax_amount', 'line_total')
    show_change_link = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer', 'status',
        'subtotal', 'tax_amount', 'total', 'created_at',
    )
    list_display_links = ('order_number',)
    list_filter = ('status', 'created_at')
    search_fields = (
        'order_number',
        'customer__user__email',
        'customer__company_name',
        'customer__user__first_name',
        'customer__user__last_name',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderLineItemInline]
    fieldsets = (
        (_('Identificación'), {
            'fields': ('order_number', 'customer', 'status', 'confirmed_at'),
        }),
        (_('Direcciones (snapshot)'), {
            'fields': ('shipping_address_snapshot', 'billing_address_snapshot'),
            'classes': ('collapse',),
            'description': _(
                'Direcciones capturadas en el momento del pedido. '
                'Completar al confirmar el pedido.'
            ),
        }),
        (_('Importes'), {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'total'),
        }),
        (_('Notas e información interna'), {
            'fields': ('notes', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(OrderLineItem)
class OrderLineItemAdmin(admin.ModelAdmin):
    list_display = (
        'product_name', 'sku', 'order', 'quantity',
        'unit_price', 'tax_rate_pct', 'tax_amount', 'line_total',
    )
    list_filter = ('order__status',)
    search_fields = (
        'product_name', 'sku',
        'order__order_number',
        'order__customer__user__email',
    )
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('order', 'variant')
