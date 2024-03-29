# Generated by Django 3.0.3 on 2020-07-26 19:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stocks", "0011_auto_20200724_2252"),
    ]

    operations = [
        migrations.CreateModel(
            name="Dividend",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateTimeField()),
                ("dividend", models.DecimalField(decimal_places=2, max_digits=20)),
                (
                    "bank",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dividends",
                        to="stocks.Bank",
                    ),
                ),
                (
                    "stock",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dividends",
                        to="stocks.Stock",
                    ),
                ),
            ],
            options={
                "verbose_name": "Dividend",
                "verbose_name_plural": "Dividends",
            },
        ),
    ]
