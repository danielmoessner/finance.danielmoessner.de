# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-31 21:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0009_auto_20180623_1530"),
    ]

    operations = [
        migrations.AlterField(
            model_name="standarduser",
            name="currency",
            field=models.CharField(choices=[("EUR", "€"), ("USD", "$")], max_length=3),
        ),
    ]
