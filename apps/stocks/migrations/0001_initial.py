# Generated by Django 3.0.3 on 2020-07-18 20:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'Bank',
                'verbose_name_plural': 'Banks',
            },
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('ticker', models.CharField(max_length=10)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stocks', to='stocks.Bank')),
            ],
            options={
                'verbose_name': 'Stock',
                'verbose_name_plural': 'Stocks',
            },
        ),
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('money_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('stock_amount', models.PositiveSmallIntegerField()),
                ('buy_or_sell', models.CharField(choices=[('BUY', 'Buy'), ('SELL', 'Sell')], max_length=50)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trades', to='stocks.Bank')),
                ('stock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trades', to='stocks.Stock')),
            ],
            options={
                'verbose_name': 'Trade',
                'verbose_name_plural': 'Trades',
            },
        ),
        migrations.CreateModel(
            name='Flow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('flow', models.DecimalField(decimal_places=2, max_digits=20)),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flows', to='stocks.Bank')),
            ],
            options={
                'verbose_name': 'Depot',
                'verbose_name_plural': 'Depots',
            },
        ),
        migrations.CreateModel(
            name='Depot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('is_active', models.BooleanField(default=False)),
                ('user', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='stock_depots', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Depot',
                'verbose_name_plural': 'Depots',
            },
        ),
        migrations.AddField(
            model_name='bank',
            name='depot',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='banks', to='stocks.Depot'),
        ),
    ]
