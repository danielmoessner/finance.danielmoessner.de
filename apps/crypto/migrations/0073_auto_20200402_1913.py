# Generated by Django 3.0.3 on 2020-04-02 17:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crypto', '0072_auto_20200402_1913'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='flow',
            unique_together={('account', 'date')},
        ),
    ]
