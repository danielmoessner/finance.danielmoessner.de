# Generated by Django 3.0.3 on 2020-03-26 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_auto_20200326_1330'),
    ]

    operations = [
        migrations.AlterField(
            model_name='standarduser',
            name='front_page',
            field=models.CharField(choices=[('BANKING', 'Banking'), ('ALTERNATIVE', 'Alternative'), ('CRYPTO', 'Crypto'), ('SETTINGS', 'Settings')], default='SETTINGS', max_length=20),
        ),
    ]
