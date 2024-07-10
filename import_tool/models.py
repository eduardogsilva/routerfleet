from django.db import models

from backup.models import BackupProfile
from router_manager.models import Router, SSHKey, SUPPORTED_ROUTER_TYPES, RouterGroup
import uuid


class CsvData(models.Model):
    raw_csv_data = models.TextField()
    import_data = models.JSONField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.name


class ImportTask(models.Model):
    csv_data = models.ForeignKey(CsvData, on_delete=models.CASCADE)
    router = models.ForeignKey(Router, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=100)
    ssh_key = models.ForeignKey(SSHKey, on_delete=models.SET_NULL, blank=True, null=True)
    ssh_key_name = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100, blank=True, null=True)
    router_group = models.ForeignKey(RouterGroup, on_delete=models.SET_NULL, blank=True, null=True)
    router_group_name = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=100)
    port = models.IntegerField(default=22)
    backup_profile = models.ForeignKey(BackupProfile, on_delete=models.SET_NULL, blank=True, null=True)
    backup_profile_name = models.CharField(max_length=100, blank=True, null=True)
    router_type = models.CharField(max_length=100, choices=SUPPORTED_ROUTER_TYPES)
    monitoring = models.BooleanField(default=True)

    import_success = models.BooleanField(default=False)
    import_error = models.BooleanField(default=False)
    import_error_message = models.TextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.name

