"""
Catalog models: products, categories, variants, images.
"""

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


class ProductCategory(BaseModel):
    """Product category."""
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name=_('Parent category')
    )
    display_order = models.IntegerField(default=0, verbose_name=_('Display order'))

    class Meta:
        verbose_name = _('Product Category')
        verbose_name_plural = _('Product Categories')
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductBrand(BaseModel):
    """Product brand/manufacturer."""
    name = models.CharField(max_length=200, verbose_name=_('Name'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    logo = models.ImageField(upload_to='brands/', null=True, blank=True, verbose_name=_('Logo'))

    class Meta:
        verbose_name = _('Product Brand')
        verbose_name_plural = _('Product Brands')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(BaseModel):
    """
    Main Product entity.
    Contains common data; pricing and stock per variant.
    """
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('Category')
    )
    brand = models.ForeignKey(
        ProductBrand,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='products',
        verbose_name=_('Brand')
    )
    sku_base = models.CharField(max_length=100, unique=True, verbose_name=_('Base SKU'))
    unit_of_measure = models.CharField(
        max_length=50,
        default='unit',
        verbose_name=_('Unit of measure'),
        help_text=_('e.g., unit, m2, box')
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Weight (kg)')
    )
    is_featured = models.BooleanField(default=False, verbose_name=_('Featured'))
    seo_title = models.CharField(max_length=255, blank=True, verbose_name=_('SEO title'))
    seo_description = models.CharField(max_length=160, blank=True, verbose_name=_('SEO description'))

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductVariant(BaseModel):
    """
    Variant of a product (e.g., color, size).
    Has its own SKU, price, and stock.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('Product')
    )
    sku = models.CharField(max_length=100, unique=True, verbose_name=_('SKU'))
    name = models.CharField(max_length=255, verbose_name=_('Variant name (e.g., Red, Large)'))
    
    # Pricing (base prices, before tax)
    price_no_tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Price without tax (€)'),
        help_text=_('Base price before VAT')
    )
    
    # Stock (can be optional if ENABLE_PUBLIC_STOCK is False)
    stock_quantity = models.IntegerField(
        default=0,
        verbose_name=_('Stock quantity'),
        help_text=_('0 = out of stock, -1 = unlimited')
    )
    
    # Images
    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True,
        verbose_name=_('Primary image')
    )
    
    display_order = models.IntegerField(default=0, verbose_name=_('Display order'))

    class Meta:
        verbose_name = _('Product Variant')
        verbose_name_plural = _('Product Variants')
        ordering = ['product', 'display_order']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name} ({self.sku})"

    def is_in_stock(self):
        """Check if variant is in stock."""
        return self.stock_quantity != 0

    def reduce_stock(self, quantity):
        """Reduce stock (for order confirmation)."""
        if self.stock_quantity > 0:
            self.stock_quantity = max(0, self.stock_quantity - quantity)
            self.save()


class ProductImage(BaseModel):
    """Additional images for a product."""
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='additional_images',
        verbose_name=_('Variant')
    )
    image = models.ImageField(upload_to='products/', verbose_name=_('Image'))
    alt_text = models.CharField(max_length=255, blank=True, verbose_name=_('Alt text'))
    display_order = models.IntegerField(default=0, verbose_name=_('Display order'))

    class Meta:
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')
        ordering = ['variant', 'display_order']

    def __str__(self):
        return f"Image for {self.variant}"
