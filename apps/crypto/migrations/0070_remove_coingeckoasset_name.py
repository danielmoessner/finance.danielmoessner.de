# Generated by Django 3.0.3 on 2020-04-01 14:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0069_coingeckoasset_coingecko_symbol'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coingeckoasset',
            name='name',
        ),
    ]