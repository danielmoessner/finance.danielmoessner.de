# Generated by Django 3.0.3 on 2020-08-14 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alternative', '0030_auto_20200815_0015'),
    ]

    operations = [
        migrations.AddField(
            model_name='alternative',
            name='profit',
            field=models.FloatField(null=True),
        ),
    ]
