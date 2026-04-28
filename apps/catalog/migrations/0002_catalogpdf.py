# Generated migration for CatalogPDF model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CatalogPDF",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated at"),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Active")),
                ("title", models.CharField(max_length=255, verbose_name="Title")),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Description"),
                ),
                (
                    "year",
                    models.IntegerField(blank=True, null=True, verbose_name="Year"),
                ),
                (
                    "pdf_file",
                    models.FileField(
                        upload_to="catalogs/pdf/", verbose_name="PDF file"
                    ),
                ),
                (
                    "cover_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="catalogs/covers/",
                        verbose_name="Cover image",
                    ),
                ),
                (
                    "brand",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="catalogs",
                        to="catalog.productbrand",
                        verbose_name="Brand",
                    ),
                ),
            ],
            options={
                "verbose_name": "Catalog PDF",
                "verbose_name_plural": "Catalog PDFs",
                "ordering": ["-year", "title"],
            },
        ),
    ]
