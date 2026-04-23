"""
Admin registrations for Accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User admin extending Django's built-in UserAdmin."""
    list_display = (
        'email', 'get_full_name', 'role', 'is_active',
        'is_staff', 'date_joined',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')

    # Extend default fieldsets to include the role field
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Información personal'), {
            'fields': ('first_name', 'last_name', 'email'),
        }),
        (_('Rol en la plataforma'), {
            'fields': ('role',),
            'description': _(
                'admin: acceso completo. '
                'commercial: acceso a gestión de clientes y pedidos. '
                'customer: acceso al área de cliente.'
            ),
        }),
        (_('Permisos'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions',
            ),
            'classes': ('collapse',),
        }),
        (_('Fechas'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name',
                'role', 'password1', 'password2',
            ),
        }),
    )
