# Generated by Django 3.0.3 on 2020-03-17 11:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('alternative', '0017_auto_20200317_1200'),
    ]

    operations = [
        migrations.RenameField(
            model_name='picture',
            old_name='f',
            new_name='invested_capital',
        ),
        migrations.RenameField(
            model_name='picture',
            old_name='g',
            new_name='profit',
        ),
        migrations.RenameField(
            model_name='picture',
            old_name='v',
            new_name='value',
        ),
    ]
