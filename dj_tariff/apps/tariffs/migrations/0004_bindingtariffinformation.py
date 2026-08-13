# Generated migration for BindingTariffInformation model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tariff', '0003_tariffcodedetail'),
    ]

    operations = [
        migrations.CreateModel(
            name='BindingTariffInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('binding_number', models.CharField(help_text='Binding tariff information number.', max_length=255, unique=True)),
                ('valid_from', models.DateField(help_text='Date from which this binding tariff information is valid.')),
                ('reasoning', models.TextField(blank=True, help_text='Reasoning for this binding tariff information.')),
                ('description', models.TextField(blank=True, help_text='Description text for this binding tariff information.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tariff_node', models.OneToOneField(help_text='GTIP tariff node associated with this binding tariff information.', on_delete=django.db.models.deletion.CASCADE, related_name='binding_tariff_info', to='tariff.tariffnode')),
            ],
            options={
                'verbose_name': 'Binding Tariff Information',
                'verbose_name_plural': 'Binding Tariff Information',
                'ordering': ['-valid_from', 'binding_number'],
                'indexes': [
                    models.Index(fields=['binding_number'], name='tariffs_bin_binding_idx'),
                    models.Index(fields=['valid_from'], name='tariffs_bin_valid_f_idx'),
                ],
            },
        ),
    ]
