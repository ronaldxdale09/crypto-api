# Generated by Django 5.1.6 on 2025-03-11 06:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_account', '0010_remove_userdetail_role_id_user_role_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdetail',
            name='uid',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
