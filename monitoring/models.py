from django.db import models
from router_manager.models import Router
import uuid


class RouterDownTime(models.Model):
    router = models.ForeignKey(Router, on_delete=models.CASCADE)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    total_down_time = models.IntegerField(default=0)  # seconds

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def save(self, *args, **kwargs):
        if self.end_time:
            self.total_down_time = int((self.end_time - self.start_time).total_seconds())
        super().save(*args, **kwargs)