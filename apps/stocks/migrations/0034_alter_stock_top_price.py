# Generated by Django 4.2.3 on 2023-08-25 21:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stocks", "0033_stock_top_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stock",
            name="top_price",
            field=models.CharField(default="", max_length=50),
            preserve_default=False,
        ),
    ]
