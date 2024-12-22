# Generated by Django 5.1.4 on 2024-12-22 14:28

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stocks", "0043_alter_stock_isin"),
    ]

    operations = [
        migrations.AddField(
            model_name="price",
            name="isin",
            field=models.CharField(
                max_length=12,
                null=True,
                validators=[django.core.validators.MinLengthValidator(12)],
                verbose_name="ISIN",
            ),
        ),
    ]
