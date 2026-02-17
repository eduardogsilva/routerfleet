from django.db import models
from router_manager.models import Router
import uuid
import hashlib
import os


class RouterBackup(models.Model):
    router = models.ForeignKey(Router, on_delete=models.CASCADE)
    success = models.BooleanField(default=False)
    error = models.BooleanField(default=False)
    backup_pending_retrieval = models.BooleanField(default=False)
    config_change_detected = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    next_retry = models.DateTimeField(blank=True, null=True)
    schedule_time = models.DateTimeField(blank=True, null=True)
    schedule_type = models.CharField(max_length=10, choices=(('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('instant', 'Instant')))
    queue_length = models.IntegerField(default=0) # Seconds
    finish_time = models.DateTimeField(blank=True, null=True)
    backup_text = models.TextField(blank=True, null=True)
    backup_text_hash = models.CharField(max_length=64, blank=True, db_index=True)
    backup_text_filename = models.CharField(max_length=255, blank=True, null=True)
    backup_binary = models.FileField(upload_to='backups/', blank=True, null=True)
    task_console_output = models.TextField(blank=True, null=True, default='')
    task_lock = models.DateTimeField(blank=True, null=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def save(self, *args, **kwargs):
        if self.backup_text:
            self.backup_text_hash = hashlib.sha256(self.backup_text.encode('utf-8')).hexdigest()
        else:
            self.backup_text_hash = ''
        super(RouterBackup, self).save(*args, **kwargs)

