# Generated by Django 4.2.3 on 2023-07-29 16:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0031_rename_type_pricefetcher_fetcher_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pricefetcher',
            name='target',
        ),
        migrations.RemoveField(
            model_name='pricefetcher',
            name='website',
        ),
    ]
