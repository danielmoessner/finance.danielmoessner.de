# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-04 20:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0012_auto_20180604_1436'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='depot',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.PROTECT, related_name='assets', to='crypto.Depot'),
            preserve_default=False,
        ),
    ]
