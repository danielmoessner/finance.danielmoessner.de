# Generated by Django 4.2.7 on 2024-03-24 20:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("overview", "0004_alter_bucket_wanted_percentage"),
        ("stocks", "0039_stock_bucket"),
    ]

    operations = [
        migrations.AddField(
            model_name="bank",
            name="bucket",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="stocks_banks",
                to="overview.bucket",
            ),
        ),
        migrations.AlterField(
            model_name="stock",
            name="bucket",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="stocks_stocks",
                to="overview.bucket",
            ),
        ),
    ]
