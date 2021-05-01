# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-25 10:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0035_remove_asset_depot'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='depots',
            field=models.ManyToManyField(related_name='assets', to='crypto.Depot'),
        ),
    ]