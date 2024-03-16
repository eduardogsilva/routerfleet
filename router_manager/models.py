from django.db import models
import uuid


class SSHKey(models.Model):
    name = models.CharField(max_length=100)
    public_key = models.TextField()
    private_key = models.TextField()

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return self.name


class Router(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=15)
    username = models.CharField(max_length=100, default='admin')
    password = models.CharField(max_length=100, null=True, blank=True)
    ssh_key = models.ForeignKey(SSHKey, on_delete=models.SET_NULL, null=True, blank=True)
    monitoring = models.BooleanField(default=True)

    router_type = models.CharField(max_length=100, choices=(('routeros', 'Mikrotik (RouterOS)'), ('openwrt', 'OpenWRT')))
    enabled = models.BooleanField(default=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return self.name


class RouterStatus(models.Model):
    router = models.OneToOneField(Router, on_delete=models.CASCADE)
    status_online = models.BooleanField(default=False)
    last_status_change = models.DateTimeField(blank=True, null=True)
    last_backup = models.DateTimeField(blank=True, null=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

