# Generated by Django 3.0.3 on 2020-07-24 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0008_auto_20200724_2242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='amount',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='stock',
            name='value',
            field=models.DecimalField(decimal_places=2, max_digits=20, null=True),
        ),
    ]