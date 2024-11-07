from django.db import models

import uuid


HOUR_CHOICES = (
    (0, '00:00'), (1, '01:00'), (2, '02:00'), (3, '03:00'), (4, '04:00'), (5, '05:00'), (6, '06:00'), (7, '07:00'),
    (8, '08:00'), (9, '09:00'), (10, '10:00'), (11, '11:00'), (12, '12:00'), (13, '13:00'), (14, '14:00'),
    (15, '15:00'), (16, '16:00'), (17, '17:00'), (18, '18:00'), (19, '19:00'), (20, '20:00'), (21, '21:00'),
    (22, '22:00'), (23, '23:00')
)


class BackupProfile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    daily_backup = models.BooleanField(default=True)
    weekly_backup = models.BooleanField(default=False)
    monthly_backup = models.BooleanField(default=False)

    daily_retention = models.IntegerField(default=7)
    weekly_retention = models.IntegerField(default=30)
    monthly_retention = models.IntegerField(default=365)
    instant_retention = models.IntegerField(default=3650)
    retain_backups_on_error = models.BooleanField(default=True)

    parameter_sensitive = models.BooleanField(default=False)
    parameter_terse = models.BooleanField(default=False)

    daily_day_monday = models.BooleanField(default=True)
    daily_day_tuesday = models.BooleanField(default=True)
    daily_day_wednesday = models.BooleanField(default=True)
    daily_day_thursday = models.BooleanField(default=True)
    daily_day_friday = models.BooleanField(default=True)
    daily_day_saturday = models.BooleanField(default=True)
    daily_day_sunday = models.BooleanField(default=True)

    weekly_day = models.CharField(max_length=10, default='sunday', choices=(('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'), ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday')))
    monthly_day = models.IntegerField(default=1, choices=((1, '1st'), (7, '7th'), (14, '14th'), (21, '21st'), (28, '28th')))

    daily_hour = models.IntegerField(default=3, choices=HOUR_CHOICES)
    weekly_hour = models.IntegerField(default=1, choices=HOUR_CHOICES)
    monthly_hour = models.IntegerField(default=0, choices=HOUR_CHOICES)

    max_retry = models.IntegerField(default=3, choices=((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')))
    retry_interval = models.IntegerField(default=30, choices=((1, '1 Minute'), (15, '15 Minutes'), (30, '30 Minutes'), (60, '1 Hour')))
    retrieve_interval = models.IntegerField(default=60, choices=((15, '15 Seconds'), (30, '30 Seconds'), (60, '1 Minute'), (900, '15 Minutes'), (1800, '30 Minutes'), (3600, '1 Hour')))
    backup_interval = models.IntegerField(default=0, choices=((0, 'No interval'), (5, '5 seconds'), (60, '1 minute')))

    profile_error_information = models.CharField(max_length=100, blank=True, null=True)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)

    def __str__(self):
        return self.name

