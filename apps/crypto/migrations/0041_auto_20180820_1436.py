# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-20 12:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0040_auto_20180812_2315'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='private_name',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='private_symbol',
        ),
    ]
