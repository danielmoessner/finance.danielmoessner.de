# Generated by Django 3.0.3 on 2020-07-29 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0018_auto_20200729_1509'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='price',
            field=models.FloatField(null=True),
        ),
    ]
