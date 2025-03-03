# Generated by Django 5.1.6 on 2025-02-27 05:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto_currency', '0001_initial'),
        ('wallet', '0004_remove_transaction_wallet_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WalletBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=8, default=0.0, max_digits=24)),
                ('cryptocurrency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crypto_currency.cryptocurrency')),
                ('wallet', models.ManyToManyField(blank=True, null=True, related_name='balances', to='wallet.wallet')),
            ],
        ),
    ]
