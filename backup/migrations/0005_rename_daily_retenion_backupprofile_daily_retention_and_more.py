# Generated by Django 5.0.3 on 2024-04-01 15:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backup', '0004_backupprofile_instant_retenion_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='backupprofile',
            old_name='daily_retenion',
            new_name='daily_retention',
        ),
        migrations.RenameField(
            model_name='backupprofile',
            old_name='instant_retenion',
            new_name='instant_retention',
        ),
        migrations.RenameField(
            model_name='backupprofile',
            old_name='monthly_retenion',
            new_name='monthly_retention',
        ),
    ]
