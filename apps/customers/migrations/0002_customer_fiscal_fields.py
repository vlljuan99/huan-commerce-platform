# Generated manually — adds fiscal_name, contact_email, fixes tax_id nullability

from django.db import migrations, models


def empty_string_to_null(apps, schema_editor):
    """Convert existing empty-string tax_ids to NULL to satisfy the unique constraint."""
    Customer = apps.get_model('customers', 'Customer')
    Customer.objects.filter(tax_id='').update(tax_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        # Step 1: allow NULL on tax_id first, then clean data
        migrations.AlterField(
            model_name='customer',
            name='tax_id',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=50,
                unique=True,
                verbose_name='Tax ID',
                help_text='CIF/NIF',
            ),
        ),
        # Step 2: convert existing '' to NULL (idempotent)
        migrations.RunPython(empty_string_to_null, migrations.RunPython.noop),
        # Step 3: fiscal_name
        migrations.AddField(
            model_name='customer',
            name='fiscal_name',
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name='Fiscal name',
                help_text='Nombre que aparece en facturas. B2C: nombre y apellidos. B2B: razón social.',
            ),
        ),
        # Step 4: contact_email
        migrations.AddField(
            model_name='customer',
            name='contact_email',
            field=models.EmailField(
                blank=True,
                verbose_name='Contact email',
                help_text='Email de contacto para facturas y comunicaciones. Puede diferir del email de acceso.',
            ),
        ),
    ]
