# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-31 20:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("crypto", "0042_auto_20180831_2135"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="timespan",
            name="period",
        ),
    ]
