# Generated by Django 3.0.3 on 2020-04-02 20:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crypto", "0073_auto_20200402_1913"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coingeckoasset",
            name="coingecko_symbol",
            field=models.CharField(max_length=10),
        ),
    ]
