# Generated by Django 4.2.7 on 2023-11-06 17:33

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("alternative", "0033_alternative_value"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="alternative",
            name="value",
        ),
    ]
