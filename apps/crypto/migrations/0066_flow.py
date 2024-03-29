# Generated by Django 3.0.3 on 2020-03-30 14:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crypto", "0065_auto_20200330_1459"),
    ]

    operations = [
        migrations.CreateModel(
            name="Flow",
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
                ("flow", models.DecimalField(decimal_places=2, max_digits=20)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="flows",
                        to="crypto.Account",
                    ),
                ),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="flows",
                        to="crypto.Asset",
                    ),
                ),
            ],
        ),
    ]
