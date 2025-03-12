from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('trading', '0001_initial'),  # Make sure this points to your last migration
    ]

    operations = [
        # This doesn't change the database, just updates Django's internal state
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='order',
                    name='is_approved',
                    field=models.BooleanField(default=True),
                ),
            ],
        ),
    ]