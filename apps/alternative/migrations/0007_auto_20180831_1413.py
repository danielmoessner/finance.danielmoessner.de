# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-31 12:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("alternative", "0006_auto_20180831_1339"),
    ]

    operations = [
        migrations.AlterField(
            model_name="picture",
            name="cr",
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=18, null=True
            ),
        ),
        migrations.AlterField(
            model_name="picture",
            name="cs",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=18, null=True
            ),
        ),
        migrations.AlterField(
            model_name="picture",
            name="f",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=18, null=True
            ),
        ),
        migrations.AlterField(
            model_name="picture",
            name="g",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=18, null=True
            ),
        ),
        migrations.AlterField(
            model_name="picture",
            name="ttwr",
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=18, null=True
            ),
        ),
        migrations.AlterField(
            model_name="picture",
            name="v",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=18, null=True
            ),
        ),
    ]
