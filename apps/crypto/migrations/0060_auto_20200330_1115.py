# Generated by Django 3.0.3 on 2020-03-30 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0059_auto_20200330_1115'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
    ]
