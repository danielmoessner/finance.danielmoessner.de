# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-31 20:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("alternative", "0010_auto_20180831_1739"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="timespan",
            name="period",
        ),
    ]
