# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-05-28 16:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0006_auto_20180415_1226'),
    ]

    operations = [
        migrations.AddField(
            model_name='intelligenttimespan',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
