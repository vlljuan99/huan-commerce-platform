from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("customers", "0003_alter_customer_company_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="customer_code",
            field=models.CharField(
                blank=True,
                max_length=20,
                verbose_name="Customer code",
                help_text="Código interno de cliente (Cod.Cliente en facturas)",
            ),
        ),
    ]
