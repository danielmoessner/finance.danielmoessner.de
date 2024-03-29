# Generated by Django 4.2.7 on 2024-02-26 13:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("overview", "0001_initial"),
        ("crypto", "0081_asset_top_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="bucket",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="crypto_items",
                to="overview.bucket",
            ),
        ),
    ]
