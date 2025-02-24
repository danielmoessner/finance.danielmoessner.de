# Generated by Django 5.1.4 on 2024-12-22 13:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stocks", "0042_stock_isin"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stock",
            name="isin",
            field=models.CharField(
                max_length=12,
                null=True,
                validators=[django.core.validators.MinLengthValidator(12)],
                verbose_name="ISIN",
            ),
        ),
    ]
