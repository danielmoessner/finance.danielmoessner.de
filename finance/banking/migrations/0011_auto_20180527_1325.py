# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-05-27 11:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('banking', '0010_auto_20180527_1323'),
    ]

    operations = [
        migrations.AlterField(
            model_name='depot',
            name='timespan',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='depots', to='banking.Timespan'),
        ),
    ]
