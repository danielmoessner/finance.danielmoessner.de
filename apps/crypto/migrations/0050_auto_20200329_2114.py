# Generated by Django 3.0.3 on 2020-03-29 19:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0049_asset_depot'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='depots',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='slug',
        ),
    ]
