# Generated by Django 3.0.3 on 2020-08-07 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0022_auto_20200807_1411'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='amount',
            field=models.DecimalField(decimal_places=3, max_digits=10, null=True),
        ),
    ]
