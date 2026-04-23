"""
Admin registrations for Invoicing app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Invoice, InvoiceLineItem, InvoiceSeries


@admin.register(InvoiceSeries)
class InvoiceSeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefix', 'next_number', 'year', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'prefix')
    fields = ('name', 'prefix', 'next_number', 'year', 'is_active')


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1
    fields = (
        'description', 'quantity', 'unit_price',
        'tax_rate', 'tax_rate_pct', 'tax_amount', 'line_total',
    )
    readonly_fields = ('tax_amount',)
    show_change_link = True


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'customer_display', 'status',
        'subtotal', 'tax_amount', 'total', 'issued_at', 'due_date',
    )
    list_display_links = ('invoice_number',)
    list_filter = ('status', 'series', 'issued_at')
    search_fields = (
        'invoice_number',
        'customer__user__email',
        'customer__company_name',
        'billing_name_snapshot',
        'tax_id_snapshot',
        'order__order_number',
    )
    readonly_fields = ('invoice_number', 'number', 'created_at', 'updated_at')
    inlines = [InvoiceLineItemInline]
    fieldsets = (
        (_('Numeración'), {
            'fields': ('series', 'number', 'invoice_number'),
        }),
        (_('Pedido y cliente'), {
            'fields': ('customer', 'order'),
        }),
        (_('Datos fiscales (snapshot)'), {
            'fields': (
                'billing_name_snapshot', 'tax_id_snapshot',
                'billing_address_snapshot',
            ),
            'description': _(
                'Datos del cliente capturados en el momento de emisión. '
                'Rellenar al pasar estado a «issued».'
            ),
        }),
        (_('Estado y fechas'), {
            'fields': ('status', 'issued_at', 'due_date'),
        }),
        (_('Importes'), {
            'fields': ('subtotal', 'tax_amount', 'total'),
        }),
        (_('Notas y documentos'), {
            'fields': ('notes', 'pdf_file'),
            'classes': ('collapse',),
        }),
        (_('Auditoría'), {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description=_('Cliente'), ordering='customer__company_name')
    def customer_display(self, obj):
        return obj.customer.display_name


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = (
        'description', 'invoice', 'quantity',
        'unit_price', 'tax_rate_pct', 'tax_amount', 'line_total',
    )
    search_fields = ('description', 'invoice__invoice_number')
    list_filter = ('invoice__status',)
    raw_id_fields = ('invoice',)
