# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-25 10:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0036_auto_20180625_1237'),
    ]

    operations = [
        migrations.RenameField(
            model_name='asset',
            old_name='name',
            new_name='private_name',
        ),
        migrations.RenameField(
            model_name='asset',
            old_name='old_symbol',
            new_name='private_symbol',
        ),
    ]
