# Generated by Django 3.1 on 2020-08-15 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0076_auto_20200815_1235'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='value',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='accountassetstats',
            name='amount',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='accountassetstats',
            name='value',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='amount',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='price',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='value',
            field=models.FloatField(null=True),
        ),
        migrations.DeleteModel(
            name='Timespan',
        ),
    ]