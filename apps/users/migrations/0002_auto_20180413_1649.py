# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-13 14:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="standarduser",
            name="currency",
            field=models.CharField(choices=[("€", "EUR"), ("$", "USD")], max_length=3),
        ),
    ]
