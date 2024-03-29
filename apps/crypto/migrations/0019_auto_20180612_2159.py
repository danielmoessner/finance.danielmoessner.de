# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-12 19:59
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("crypto", "0018_auto_20180612_2153"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="movie",
            field=models.OneToOneField(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="undefined_2",
                to="crypto.Movie",
            ),
        ),
        migrations.AlterField(
            model_name="asset",
            name="acc_movie",
            field=models.OneToOneField(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="undefined_1",
                to="crypto.Movie",
            ),
        ),
    ]
