# Generated by Django 5.0.3 on 2024-03-16 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('router_manager', '0005_alter_sshkey_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='routergroup',
            name='default_group',
            field=models.BooleanField(default=False),
        ),
    ]
