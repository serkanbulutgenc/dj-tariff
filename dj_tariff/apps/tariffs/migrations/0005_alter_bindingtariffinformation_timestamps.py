# Migration to add editable=False to timestamp fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tariff', '0004_bindingtariffinformation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bindingtariffinformation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, editable=False),
        ),
        migrations.AlterField(
            model_name='bindingtariffinformation',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, editable=False),
        ),
    ]
