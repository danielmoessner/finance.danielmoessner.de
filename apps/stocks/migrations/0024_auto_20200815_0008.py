# Generated by Django 3.0.3 on 2020-08-14 22:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0023_auto_20200807_1509'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stock',
            options={'ordering': ['name'], 'verbose_name': 'Stock', 'verbose_name_plural': 'Stocks'},
        ),
    ]