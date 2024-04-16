from django.db import models
from router_manager.models import Router
from backup_data.models import RouterBackup
import uuid


class Notification(models.Model):
    notification_type = models.CharField(choices=(('status_online', 'Status change: Online'), ('status_offline', 'Status change: Offline'), ('backup_fail', 'Backup failed')), max_length=14)
    router = models.ForeignKey(Router, on_delete=models.CASCADE, blank=True, null=True)
    router_backup = models.ForeignKey(RouterBackup, on_delete=models.CASCADE, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)


class MessageChannel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField(default=True)
    channel_type = models.CharField(
        max_length=100, choices=(
            ('callmebot', 'CallMeBot (WhatsApp)'), ('telegram', 'Telegram'),
        )
    )
    destination = models.CharField(max_length=100, blank=True, null=True)
    token = models.CharField(max_length=100, blank=True, null=True)

    status_change_offline = models.BooleanField(default=True)
    status_change_online = models.BooleanField(default=True)
    backup_fail = models.BooleanField(default=True)
    daily_status_report = models.BooleanField(default=True)
    daily_backup_report = models.BooleanField(default=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name + ' (' + self.channel_type + ')'


class Message(models.Model):
    channel = models.ForeignKey(MessageChannel, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=100, choices=(
        ('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'),
    ), default='pending')
    retry_count = models.IntegerField(default=0)
    next_retry = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    error_status_code = models.IntegerField(blank=True, null=True)
    completed = models.DateTimeField(blank=True, null=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)


class MessageSettings(models.Model):
    name = models.CharField(max_length=16, default='message_settings', unique=True)
    max_length = models.IntegerField(default=2000)
    max_retry = models.IntegerField(default=3)
    retry_interval = models.IntegerField(default=60)  # in seconds
    concatenate_status_change = models.BooleanField(default=True)
    status_change_delay = models.IntegerField(default=120)  # in seconds
    concatenate_backup_fails = models.BooleanField(default=True)
    backup_fails_delay = models.IntegerField(default=600)  # in seconds
    last_daily_status_report = models.DateTimeField(blank=True, null=True)
    last_daily_backup_report = models.DateTimeField(blank=True, null=True)
    daily_report_time = models.CharField(max_length=5, default='07:00')

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

