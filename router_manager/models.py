from django.db import models
from backup.models import BackupProfile
import uuid

SUPPORTED_ROUTER_TYPES = (
    ('monitoring', 'Monitoring Only'),
    ('routeros', 'Mikrotik (RouterOS)'),
    ('routeros-branded', 'Mikrotik (Branded)'),
    ('openwrt', 'OpenWRT'),
    ('ubiquiti-airos', 'Ubiquiti airOS')
)


class SSHKey(models.Model):
    name = models.CharField(max_length=100, unique=True)
    public_key = models.TextField()
    private_key = models.TextField()

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return self.name


class Router(models.Model):
    name = models.CharField(max_length=100, unique=True)
    internal_notes = models.TextField(null=True, blank=True)
    address = models.CharField(max_length=100)
    port = models.IntegerField(default=22)
    username = models.CharField(max_length=100, default='admin')
    password = models.CharField(max_length=100, null=True, blank=True)
    ssh_key = models.ForeignKey(SSHKey, on_delete=models.SET_NULL, null=True, blank=True)
    monitoring = models.BooleanField(default=True)
    backup_profile = models.ForeignKey(BackupProfile, on_delete=models.SET_NULL, null=True, blank=True)
    router_type = models.CharField(max_length=100, choices=SUPPORTED_ROUTER_TYPES)
    enabled = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return self.name


class RouterStatus(models.Model):
    router = models.OneToOneField(Router, on_delete=models.CASCADE)
    status_online = models.BooleanField(default=True)
    last_status_change = models.DateTimeField(blank=True, null=True)
    last_backup = models.DateTimeField(blank=True, null=True)
    last_backup_failed = models.DateTimeField(blank=True, null=True)
    backup_lock = models.DateTimeField(blank=True, null=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)


class RouterGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    default_group = models.BooleanField(default=False)
    internal_notes = models.TextField(null=True, blank=True)
    routers = models.ManyToManyField(Router, blank=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return self.name


class BackupSchedule(models.Model):
    router = models.OneToOneField(Router, on_delete=models.CASCADE)
    next_daily_backup = models.DateTimeField(null=True, blank=True)
    next_weekly_backup = models.DateTimeField(null=True, blank=True)
    next_monthly_backup = models.DateTimeField(null=True, blank=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)


class RouterInformation(models.Model):
    router = models.OneToOneField(Router, on_delete=models.CASCADE)

    success = models.BooleanField(default=False)
    error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    next_retry = models.DateTimeField(blank=True, null=True)
    last_retrieval = models.DateTimeField(blank=True, null=True)

    model_name = models.CharField(max_length=100, null=True, blank=True)
    model_version = models.CharField(max_length=100, null=True, blank=True)
    serial_number = models.CharField(max_length=100, null=True, blank=True)

    os_version = models.CharField(max_length=100, null=True, blank=True)
    firmware_version = models.CharField(max_length=100, null=True, blank=True)
    architecture = models.CharField(max_length=100, null=True, blank=True)
    cpu = models.CharField(max_length=100, null=True, blank=True)

    json_data = models.TextField(null=True, blank=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return str(self.router)
