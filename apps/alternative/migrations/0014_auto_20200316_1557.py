# Generated by Django 3.0.3 on 2020-03-16 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alternative', '0013_remove_flow_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flow',
            name='date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='value',
            name='date',
            field=models.DateTimeField(),
        ),
    ]