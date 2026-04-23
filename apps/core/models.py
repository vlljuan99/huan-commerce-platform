"""
Core models: base classes and shared utilities.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class BrandingSettings(models.Model):
    """
    Branding configuration stored in the database, per instance.
    Takes priority over branding.json when fields are set.
    Manage from Django Admin → Core → Branding settings.
    """

    instance_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Instance ID'),
        help_text=_('Debe coincidir con HUAN_INSTANCE, e.g. helvagres_demo'),
    )

    commercial_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Nombre comercial'),
    )
    tagline = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Tagline'),
    )

    logo = models.ImageField(
        upload_to='branding/logos/',
        null=True,
        blank=True,
        verbose_name=_('Logo'),
        help_text=_('PNG o SVG recomendado. Altura óptima: 36-48 px.'),
    )
    favicon = models.ImageField(
        upload_to='branding/favicons/',
        null=True,
        blank=True,
        verbose_name=_('Favicon'),
        help_text=_('ICO o PNG cuadrado, 32×32 px.'),
    )

    # Colors — vacío = usa el valor de branding.json
    color_primary = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Color primario'),
        help_text=_('Hex, e.g. #1a3a2a. Vacío = usa branding.json.'),
    )
    color_primary_light = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Color primario claro'),
        help_text=_('Hex, e.g. #2a5a40'),
    )
    color_accent = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Color de acento'),
        help_text=_('Hex, e.g. #c8a84b'),
    )
    color_accent_light = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Color de acento claro'),
        help_text=_('Hex, e.g. #e2c97a'),
    )

    class Meta:
        verbose_name = _('Branding settings')
        verbose_name_plural = _('Branding settings')

    def __str__(self):
        return f'Branding: {self.instance_id}'

    def as_dict(self) -> dict:
        """
        Devuelve un dict con el mismo esquema que branding.json.
        Solo incluye los campos que tienen valor definido.
        """
        data: dict = {}
        if self.commercial_name:
            data['commercial_name'] = self.commercial_name
        if self.tagline:
            data['tagline'] = self.tagline
        if self.logo:
            data['logo'] = self.logo.url
        if self.favicon:
            data['favicon'] = self.favicon.url

        colors: dict = {}
        if self.color_primary:
            colors['primary'] = self.color_primary
        if self.color_primary_light:
            colors['primary_light'] = self.color_primary_light
        if self.color_accent:
            colors['accent'] = self.color_accent
        if self.color_accent_light:
            colors['accent_light'] = self.color_accent_light
        if colors:
            data['colors'] = colors

        return data


class TimeStampedModel(models.Model):
    """
    Abstract model that automatically tracks creation and modification times.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    class Meta:
        abstract = True


class ActiveModel(models.Model):
    """
    Abstract model that tracks active/inactive state.
    Useful for soft deletes and logical deactivation.
    """
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel, ActiveModel):
    """
    Combined base model with timestamps and active state.
    Most models should inherit from this.
    """

    class Meta:
        abstract = True
