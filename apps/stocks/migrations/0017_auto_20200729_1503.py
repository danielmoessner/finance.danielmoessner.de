# Generated by Django 3.0.3 on 2020-07-29 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0016_auto_20200729_1441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bank',
            name='balance',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='bank',
            name='value',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='depot',
            name='balance',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='depot',
            name='invested_capital',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='depot',
            name='value',
            field=models.FloatField(null=True),
        ),
    ]
