"""
Admin registrations for Customers app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Customer, CustomerAddress


class CustomerAddressInline(admin.StackedInline):
    model = CustomerAddress
    extra = 0
    fields = (
        ('name', 'address_type', 'is_default'),
        'street_address',
        ('city', 'postal_code', 'region'),
        'country',
        'is_active',
    )
    show_change_link = True


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'display_name', 'user_email', 'segment', 'tax_id',
        'phone', 'contact_email', 'is_active', 'created_at',
    )
    list_display_links = ('display_name',)
    list_filter = ('segment', 'is_active', 'created_at')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name',
        'company_name', 'fiscal_name', 'tax_id', 'phone', 'contact_email',
    )
    readonly_fields = ('created_at', 'updated_at', 'billing_name')
    inlines = [CustomerAddressInline]
    fieldsets = (
        (_('Identificación'), {
            'fields': ('user', 'segment'),
        }),
        (_('Datos comerciales'), {
            'fields': ('company_name', 'phone', 'contact_email'),
            'description': _('Información de contacto y nombre comercial visible'),
        }),
        (_('Datos fiscales'), {
            'fields': ('fiscal_name', 'tax_id', 'billing_name'),
            'description': _('Datos que aparecerán en facturas. billing_name es el nombre calculado automáticamente.'),
        }),
        (_('Notas internas'), {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
        (_('Estado y auditoría'), {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description=_('Email'), ordering='user__email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description=_('Nombre'), ordering='company_name')
    def display_name(self, obj):
        return obj.display_name


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'customer', 'address_type', 'city',
        'postal_code', 'country', 'is_default', 'is_active',
    )
    list_filter = ('address_type', 'is_default', 'is_active', 'country')
    search_fields = (
        'customer__user__email', 'customer__company_name',
        'name', 'street_address', 'city', 'postal_code',
    )
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('customer', 'name', 'address_type', 'is_default'),
        }),
        (_('Dirección'), {
            'fields': ('street_address', ('city', 'postal_code'), 'region', 'country'),
        }),
        (_('Estado'), {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
