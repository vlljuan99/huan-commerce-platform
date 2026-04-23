"""
Admin registrations for core app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import BrandingSettings


@admin.register(BrandingSettings)
class BrandingSettingsAdmin(admin.ModelAdmin):
    list_display = ('instance_id', 'commercial_name', 'logo_preview', 'color_swatches')
    readonly_fields = ('logo_preview', 'favicon_preview', 'color_swatches')

    fieldsets = (
        (_('Instancia'), {
            'fields': ('instance_id',),
            'description': _(
                'Debe coincidir exactamente con el valor de HUAN_INSTANCE. '
                'Vacío en un campo = usa el valor de branding.json como fallback.'
            ),
        }),
        (_('Identidad'), {
            'fields': ('commercial_name', 'tagline'),
        }),
        (_('Logo y favicon'), {
            'fields': ('logo', 'logo_preview', 'favicon', 'favicon_preview'),
        }),
        (_('Colores de marca'), {
            'fields': (
                'color_primary', 'color_primary_light',
                'color_accent', 'color_accent_light',
                'color_swatches',
            ),
            'description': _(
                'Formato hexadecimal, e.g. #1a3a2a. '
                'Deja vacío para heredar el valor de branding.json.'
            ),
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="height:36px;border:1px solid #e2e8f0;border-radius:4px;padding:4px;">',
                obj.logo.url,
            )
        return _('Sin logo subido')
    logo_preview.short_description = _('Vista previa logo')

    def favicon_preview(self, obj):
        if obj.favicon:
            return format_html(
                '<img src="{}" style="height:32px;border:1px solid #e2e8f0;border-radius:4px;padding:4px;">',
                obj.favicon.url,
            )
        return _('Sin favicon subido')
    favicon_preview.short_description = _('Vista previa favicon')

    def color_swatches(self, obj):
        colors = [
            (obj.color_primary,       'Primario'),
            (obj.color_primary_light, 'Primario claro'),
            (obj.color_accent,        'Acento'),
            (obj.color_accent_light,  'Acento claro'),
        ]
        swatches = ''.join(
            f'<span title="{label}: {color}" style="'
            f'display:inline-block;width:32px;height:32px;'
            f'background:{color};border:1px solid #ccc;border-radius:4px;'
            f'margin-right:6px;" ></span>'
            for color, label in colors
            if color
        )
        return format_html(swatches) if swatches else _('Sin colores definidos en BD')
    color_swatches.short_description = _('Colores actuales')

