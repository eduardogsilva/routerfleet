import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone

from router_manager.models import Router, RouterGroup, SUPPORTED_ROUTER_TYPES


class Command(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)

    enabled = models.BooleanField(default=True)

    capture_output = models.BooleanField(default=False)
    max_retry = models.IntegerField(default=3)
    retry_interval = models.IntegerField(default=30, help_text="Retry interval in seconds")

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def __str__(self) -> str:
        return self.name


class CommandSchedule(models.Model):
    command = models.ForeignKey(Command, on_delete=models.PROTECT, related_name="schedules")
    router = models.ManyToManyField(Router, blank=True, related_name="command_schedules")
    router_group = models.ManyToManyField(RouterGroup, blank=True, related_name="command_schedules")
    enabled = models.BooleanField(default=True)

    start_at = models.DateTimeField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    repeat_interval = models.IntegerField(help_text="Repeat interval in minutes", default=0)

    last_run = models.DateTimeField(blank=True, null=True)
    next_run = models.DateTimeField(blank=True, null=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    @property
    def calculate_next_run(self):
        if not self.enabled or self.repeat_interval <= 0:
            return None

        now = timezone.now()
        base = self.start_at if self.start_at else now

        if base <= now:
            delta = now - base
            intervals_passed = int(delta.total_seconds() / 60 / self.repeat_interval) + 1
            next_run = base + timedelta(minutes=self.repeat_interval * intervals_passed)
        else:
            next_run = base

        if self.end_at and next_run > self.end_at:
            return None

        return next_run

    def update_next_run(self):
        self.next_run = self.calculate_next_run
        self.save(update_fields=["next_run"])
        return self.next_run


class CommandVariant(models.Model):
    command = models.ForeignKey(Command, on_delete=models.PROTECT, related_name="variants")
    router_type = models.CharField(max_length=100, choices=SUPPORTED_ROUTER_TYPES)
    payload = models.TextField()

    enabled = models.BooleanField(default=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["command", "router_type"],
                name="uniq_command_variant_per_router_type",
            )
        ]
        indexes = [
            models.Index(fields=["router_type", "enabled"]),
        ]

    def __str__(self) -> str:
        return f"{self.command.name} ({self.router_type})"


class CommandJob(models.Model):
    command = models.ForeignKey(Command, on_delete=models.PROTECT, related_name="jobs")
    user_source = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    user_source_name = models.CharField(max_length=150, blank=True, null=True)
    exec_source = models.CharField(max_length=100, choices=(('schedule', 'Schedule'), ('manual', 'Manual')), default='manual')
    completed = models.DateTimeField(blank=True, null=True)
    task_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    aborted_count = models.PositiveIntegerField(default=0)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def update_counters(self):
        tasks = self.tasks.aggregate(
            total=Count('id'),
            success=Count('id', filter=Q(status='success')),
            error=Count('id', filter=Q(status='error')),
            aborted=Count('id', filter=Q(status='aborted')),
        )
        self.task_count = tasks['total']
        self.success_count = tasks['success']
        self.error_count = tasks['error']
        self.aborted_count = tasks['aborted']

        update_fields = ['task_count', 'success_count', 'error_count', 'aborted_count']

        finished_count = tasks['success'] + tasks['error'] + tasks['aborted']
        if finished_count >= tasks['total'] and not self.completed:
            self.completed = timezone.now()
            update_fields.append('completed')

        self.save(update_fields=update_fields)

    @property
    def progress_percentage(self):
        if self.task_count == 0:
            return 0
        return int(((self.success_count + self.error_count) / self.task_count) * 100)


class CommandTask(models.Model):
    job = models.ForeignKey(CommandJob, on_delete=models.CASCADE, related_name="tasks")
    command_variant = models.ForeignKey(CommandVariant, on_delete=models.SET_NULL, null=True, blank=True)
    router = models.ForeignKey(Router, on_delete=models.SET_NULL, blank=True, null=True)
    router_name = models.CharField(max_length=100, blank=True, null=True)
    router_uuid = models.UUIDField()

    command_payload = models.TextField(blank=True, null=True)
    command_executed = models.TextField(blank=True, null=True)
    command_output = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=100, choices=(('pending', 'Pending'), ('error', 'Error'), ('success', 'Success'), ('aborted', 'Aborted')), default='pending')
    retry_count = models.PositiveIntegerField(default=0)
    next_retry = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "router_uuid"],
                name="uniq_commandtask_job_router_uuid",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "next_retry"]),
            models.Index(fields=["router_uuid", "created"]),
            models.Index(fields=["job", "status"]),
        ]

    def save(self, *args, **kwargs):
        if self.router:
            self.router_uuid = self.router.uuid
            self.router_name = self.router.name
        self.full_clean()
        super().save(*args, **kwargs)
        self.job.update_counters()

    def __str__(self) -> str:
        return f"{self.job.command.name} -> {self.router_name or self.router_uuid} ({self.status})"