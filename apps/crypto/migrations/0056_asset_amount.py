# Generated by Django 3.0.3 on 2020-03-29 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0055_auto_20200329_2202'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True),
        ),
    ]