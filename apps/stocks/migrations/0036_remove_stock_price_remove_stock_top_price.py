# Generated by Django 4.2.4 on 2023-08-26 21:31

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("stocks", "0035_alter_stock_top_price"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="stock",
            name="price",
        ),
        migrations.RemoveField(
            model_name="stock",
            name="top_price",
        ),
    ]
