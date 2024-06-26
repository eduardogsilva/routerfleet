# Generated by Django 5.0.3 on 2024-03-15 21:08

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SSHKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('public_key', models.TextField()),
                ('private_key', models.TextField()),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Router',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('address', models.CharField(max_length=15)),
                ('username', models.CharField(default='admin', max_length=100)),
                ('password', models.CharField(max_length=100)),
                ('monitoring', models.BooleanField(default=True)),
                ('router_type', models.CharField(choices=[('routeros', 'Mikrotik (RouterOS)'), ('openwrt', 'OpenWRT')], max_length=100)),
                ('enabled', models.BooleanField(default=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('ssh_key', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='router_manager.sshkey')),
            ],
        ),
    ]
