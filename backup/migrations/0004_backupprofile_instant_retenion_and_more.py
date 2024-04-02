# Generated by Django 5.0.3 on 2024-04-01 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backup', '0003_alter_backupprofile_retry_interval'),
    ]

    operations = [
        migrations.AddField(
            model_name='backupprofile',
            name='instant_retenion',
            field=models.IntegerField(default=3650),
        ),
        migrations.AddField(
            model_name='backupprofile',
            name='retrieve_interval',
            field=models.IntegerField(choices=[(1, '1 Minute'), (15, '15 Minutes'), (30, '30 Minutes'), (60, '1 Hour')], default=1),
        ),
    ]
