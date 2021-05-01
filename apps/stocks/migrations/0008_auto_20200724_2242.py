# Generated by Django 3.0.3 on 2020-07-24 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0007_price_exchange'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='amount',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='stock',
            name='value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
            preserve_default=False,
        ),
    ]