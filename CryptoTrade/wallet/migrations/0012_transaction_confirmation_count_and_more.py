# Generated by Django 5.1.6 on 2025-03-04 14:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crypto_currency', '0005_cryptocurrency_last_updated_cryptocurrency_logo_url_and_more'),
        ('wallet', '0011_transaction_cryptocurrency_transaction_network_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='confirmation_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='transaction',
            name='estimated_completion_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='memo',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='status',
            field=models.CharField(blank=True, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('processing', 'Processing'), ('confirming', 'Confirming')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='type',
            field=models.CharField(blank=True, choices=[('deposit', 'Deposit'), ('withdraw', 'Withdraw'), ('transfer', 'Transfer'), ('send', 'Send')], max_length=20, null=True),
        ),
        migrations.CreateModel(
            name='NetworkFee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fee_rate', models.DecimalField(decimal_places=8, max_digits=24)),
                ('fee_speed', models.CharField(choices=[('slow', 'Slow'), ('standard', 'Standard'), ('fast', 'Fast')], default='standard', max_length=10)),
                ('estimated_time', models.CharField(blank=True, max_length=50, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cryptocurrency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crypto_currency.cryptocurrency')),
                ('network', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crypto_currency.network')),
            ],
            options={
                'unique_together': {('network', 'cryptocurrency', 'fee_speed')},
            },
        ),
    ]
