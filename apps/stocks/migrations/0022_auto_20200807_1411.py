# Generated by Django 3.0.3 on 2020-08-07 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0021_auto_20200807_1352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trade',
            name='stock_amount',
            field=models.DecimalField(decimal_places=3, max_digits=10),
        ),
    ]