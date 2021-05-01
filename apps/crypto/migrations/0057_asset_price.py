# Generated by Django 3.0.3 on 2020-03-30 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0056_asset_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True),
        ),
    ]