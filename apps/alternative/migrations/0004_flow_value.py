# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-29 11:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alternative', '0003_auto_20180828_1656'),
    ]

    operations = [
        migrations.AddField(
            model_name='flow',
            name='value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
