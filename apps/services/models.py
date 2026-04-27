"""
Services app: construction and installation services offered alongside products.
"""

from decimal import Decimal

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Company(models.Model):
    """
    A company that provides services — either our own company or an associated partner.
    """
    name = models.CharField(max_length=200, verbose_name=_("Nombre"))
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True, verbose_name=_("Descripción"))
    logo = models.ImageField(upload_to="companies/logos/", null=True, blank=True, verbose_name=_("Logo"))
    address = models.TextField(blank=True, verbose_name=_("Dirección"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Teléfono"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    website = models.URLField(blank=True, verbose_name=_("Web"))
    is_own = models.BooleanField(
        default=False,
        verbose_name=_("Es nuestra empresa"),
        help_text=_("Marcar si es la empresa gestora de esta plataforma"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Activa"))

    class Meta:
        verbose_name = _("Empresa")
        verbose_name_plural = _("Empresas")
        ordering = ["-is_own", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ServiceCategory(models.Model):
    """Category of construction/installation service."""
    name = models.CharField(max_length=100, verbose_name=_("Nombre"))
    slug = models.SlugField(max_length=120, unique=True)
    display_order = models.PositiveSmallIntegerField(default=0, verbose_name=_("Orden"))
    is_active = models.BooleanField(default=True, verbose_name=_("Activa"))

    class Meta:
        verbose_name = _("Categoría de servicio")
        verbose_name_plural = _("Categorías de servicio")
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Service(models.Model):
    """A single construction/installation service that can be added to the cart."""

    UNIT_CHOICES = [
        ("ud", _("Unidad")),
        ("m2", _("m²")),
        ("ml", _("Metro lineal")),
        ("h",  _("Hora")),
        ("m3", _("m³")),
    ]

    name = models.CharField(max_length=200, verbose_name=_("Nombre"))
    slug = models.SlugField(max_length=220, unique=True)
    sku = models.CharField(max_length=100, blank=True, verbose_name=_("Código"))
    description = models.TextField(blank=True, verbose_name=_("Descripción"))

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
        verbose_name=_("Categoría"),
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
        verbose_name=_("Empresa"),
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Precio sin IVA (€)"),
    )
    unit = models.CharField(
        max_length=5,
        choices=UNIT_CHOICES,
        default="ud",
        verbose_name=_("Unidad"),
    )

    image = models.ImageField(
        upload_to="services/images/",
        null=True,
        blank=True,
        verbose_name=_("Imagen"),
    )
    is_featured = models.BooleanField(default=False, verbose_name=_("Destacado"))
    is_active = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        verbose_name = _("Servicio")
        verbose_name_plural = _("Servicios")
        ordering = ["category__display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def price_display(self):
        return f"{self.price} € / {self.get_unit_display()}"
