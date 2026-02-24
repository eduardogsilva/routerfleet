import time
from datetime import datetime, timedelta

from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from backup.models import BackupProfile
from backup_data.models import RouterBackup
from message_center.functions import notify_backup_fail, notify_backup_task_lock_expired
from message_center.models import Message
from router_manager.models import Router, BackupSchedule, RouterStatus
from routerlib.backup_functions import perform_backup, append_task_console_output


def next_weekday(now, weekday, hour):
    now = timezone.localtime(timezone.now())
    days_ahead = weekday - now.weekday()
    if days_ahead < 0 or (days_ahead == 0 and now.hour >= hour):
        days_ahead += 7
    next_backup = now + timedelta(days=days_ahead)
    next_backup = next_backup.replace(hour=hour, minute=0, second=0, microsecond=0)
    return next_backup


def find_next_active_day(start_date, active_days, backup_hour):
    now = timezone.localtime()
    for i in range(7):
        potential_date = timezone.localtime(start_date + timedelta(days=i))
        weekday = potential_date.weekday()
        if active_days[weekday]:
            next_active_date = potential_date.replace(hour=backup_hour, minute=0, second=0, microsecond=0)
            if next_active_date > now:
                return next_active_date
            if i == 0 and now.hour >= backup_hour:
                continue
    return None


def calculate_next_backup(backup_profile):
    now = timezone.now()

    if backup_profile.daily_backup:
        weekdays_enabled = [
            backup_profile.daily_day_monday,
            backup_profile.daily_day_tuesday,
            backup_profile.daily_day_wednesday,
            backup_profile.daily_day_thursday,
            backup_profile.daily_day_friday,
            backup_profile.daily_day_saturday,
            backup_profile.daily_day_sunday,
        ]
        next_daily_backup = find_next_active_day(now, weekdays_enabled, backup_profile.daily_hour)
    else:
        next_daily_backup = None

    if backup_profile.weekly_backup:
        weekday = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(backup_profile.weekly_day)
        next_weekly_backup = next_weekday(now, weekday, backup_profile.weekly_hour)
    else:
        next_weekly_backup = None

    if backup_profile.monthly_backup:
        potential_monthly_backup = datetime(year=now.year, month=now.month, day=backup_profile.monthly_day,
                                            hour=backup_profile.monthly_hour, tzinfo=timezone.get_current_timezone())
        if potential_monthly_backup <= now:
            month_increment = 1 if now.month < 12 else -11
            year_increment = 0 if now.month < 12 else 1
            next_monthly_backup = potential_monthly_backup.replace(year=now.year + year_increment,
                                                                   month=now.month + month_increment)
        else:
            next_monthly_backup = potential_monthly_backup
    else:
        next_monthly_backup = None

    return next_daily_backup, next_weekly_backup, next_monthly_backup


def view_cron_generate_backup_schedule(request):
    data = {
        'backup_schedule_created': 0,
        'daily_backup_schedule_created': 0,
        'weekly_backup_schedule_created': 0,
        'monthly_backup_schedule_created': 0,
        'daily_backup_schedule_removed': 0,
        'weekly_backup_schedule_removed': 0,
        'monthly_backup_schedule_removed': 0
    }

    for router in Router.objects.filter(backupschedule__isnull=True):
        new_backup_schedule, _ = BackupSchedule.objects.get_or_create(router=router)
        data['backup_schedule_created'] += 1

    for backup_profile in BackupProfile.objects.all():
        backup_schedule_list = BackupSchedule.objects.filter(router__backup_profile=backup_profile)
        next_daily_backup, next_weekly_backup, next_monthly_backup = calculate_next_backup(backup_profile)

        if backup_profile.daily_backup and not next_daily_backup:
            backup_profile.profile_error_information = 'Error calculating next daily backup. Check profile settings'
            backup_profile.save()
        if backup_profile.weekly_backup and not next_weekly_backup:
            backup_profile.profile_error_information = 'Error calculating next weekly backup. Check profile settings'
            backup_profile.save()
        if backup_profile.monthly_backup and not next_monthly_backup:
            backup_profile.profile_error_information = 'Error calculating next monthly backup. Check profile settings'
            backup_profile.save()

        if backup_profile.daily_backup:
            daily_schedule_list = backup_schedule_list.filter(next_daily_backup__isnull=True)
            for schedule in daily_schedule_list:
                schedule.next_daily_backup = next_daily_backup
                schedule.save()
                data['daily_backup_schedule_created'] += 1
        else:
            daily_schedule_list = backup_schedule_list.filter(next_daily_backup__isnull=False)
            for schedule in daily_schedule_list:
                schedule.next_daily_backup = None
                schedule.save()
                data['daily_backup_schedule_removed'] += 1

        if backup_profile.weekly_backup:
            weekly_schedule_list = backup_schedule_list.filter(next_weekly_backup__isnull=True)
            for schedule in weekly_schedule_list:
                schedule.next_weekly_backup = next_weekly_backup
                schedule.save()
                data['weekly_backup_schedule_created'] += 1
        else:
            weekly_schedule_list = backup_schedule_list.filter(next_weekly_backup__isnull=False)
            for schedule in weekly_schedule_list:
                schedule.next_weekly_backup = None
                schedule.save()
                data['weekly_backup_schedule_removed'] += 1

        if backup_profile.monthly_backup:
            monthly_schedule_list = backup_schedule_list.filter(next_monthly_backup__isnull=True)
            for schedule in monthly_schedule_list:
                schedule.next_monthly_backup = next_monthly_backup
                schedule.save()
                data['monthly_backup_schedule_created'] += 1
        else:
            monthly_schedule_list = backup_schedule_list.filter(next_monthly_backup__isnull=False)
            for schedule in monthly_schedule_list:
                schedule.next_monthly_backup = None
                schedule.save()
                data['monthly_backup_schedule_removed'] += 1
    return JsonResponse(data)


def create_backup_tasks_from_schedule_list(schedule_list, schedule_type):
    tasks_created = 0
    for schedule in schedule_list:
        if schedule_type == 'daily':
            schedule_time = schedule.next_daily_backup
            schedule.next_daily_backup = None
        elif schedule_type == 'weekly':
            schedule_time = schedule.next_weekly_backup
            schedule.next_weekly_backup = None
        elif schedule_type == 'monthly':
            schedule_time = schedule.next_monthly_backup
            schedule.next_monthly_backup = None
        else:
            return
        schedule.save()

        backup = RouterBackup.objects.create(
            router=schedule.router, schedule_time=schedule_time, schedule_type=schedule_type
        )
        tasks_created += 1
        backup.save()
        backup.router.routerstatus.backup_lock = backup.schedule_time
        backup.router.routerstatus.save()

    return tasks_created


def view_cron_create_backup_tasks(request):
    data = {
        'daily_backup_tasks_created': 0,
        'weekly_backup_tasks_created': 0,
        'monthly_backup_tasks_created': 0
    }
    # Priorize monthly, then weekly, then daily.
    monthly_pending_schedule_list = BackupSchedule.objects.filter(
        next_monthly_backup__lte=timezone.now(), router__enabled=True, router__routerstatus__backup_lock__isnull=True
    ).filter(
        Q(router__monitoring=False) | Q(router__monitoring=True, router__routerstatus__status_online=True)
    )
    data['monthly_backup_tasks_created'] = create_backup_tasks_from_schedule_list(
        monthly_pending_schedule_list, 'monthly'
    )

    weekly_pending_schedule_list = BackupSchedule.objects.filter(
        next_weekly_backup__lte=timezone.now(), router__enabled=True, router__routerstatus__backup_lock__isnull=True
    ).filter(
        Q(router__monitoring=False) | Q(router__monitoring=True, router__routerstatus__status_online=True)
    )
    data['weekly_backup_tasks_created'] = create_backup_tasks_from_schedule_list(
        weekly_pending_schedule_list, 'weekly'
    )

    daily_pending_schedule_list = BackupSchedule.objects.filter(
        next_daily_backup__lte=timezone.now(), router__enabled=True, router__routerstatus__backup_lock__isnull=True
    ).filter(
        Q(router__monitoring=False) | Q(router__monitoring=True, router__routerstatus__status_online=True)
    )
    data['daily_backup_tasks_created'] = create_backup_tasks_from_schedule_list(
        daily_pending_schedule_list, 'daily'
    )

    return JsonResponse(data)


def view_cron_perform_backup_tasks(request):
    data = {
        'backup_tasks_performed': 0
    }
    max_execution_time = 45  # seconds
    execution_start_time = timezone.now()
    pending_backup_list = RouterBackup.objects.filter(success=False, error=False, task_lock__isnull=True).filter(
        Q(schedule_time__lte=timezone.now(), next_retry__isnull=True) | Q(next_retry__lte=timezone.now())
    ).filter(
        Q(router__monitoring=False) | Q(router__monitoring=True, router__routerstatus__status_online=True)
    )

    for backup in pending_backup_list:
        backup.task_lock = timezone.now()
        backup.save(update_fields=["task_lock"])
        perform_backup(backup)
        data['backup_tasks_performed'] += 1
        backup.task_lock = None
        backup.save(update_fields=["task_lock"])

        if backup.router.backup_profile.backup_interval >= 60:
            break
        else:
            if timezone.now() - execution_start_time > timedelta(seconds=max_execution_time):
                break
            else:
                if backup.router.backup_profile.backup_interval > 0:
                    time.sleep(backup.router.backup_profile.backup_interval)
                if timezone.now() - execution_start_time > timedelta(seconds=max_execution_time):
                    break

    return JsonResponse(data)


def view_cron_housekeeping(request):
    max_backup_task_age = timezone.now() - timedelta(hours=18)
    max_backup_task_lock = timezone.now() - timedelta(hours=6)
    max_command_lock_age = timezone.now() - timedelta(hours=2)
    data = {
        'backup_tasks_expired': 0,
        'backup_locks_removed': 0,
        'backup_task_locks_expired': 0,
        'command_locks_removed': 0,
        'messages_removed': 0,
    }

    for backup in RouterBackup.objects.filter(task_lock__lt=max_backup_task_lock, success=False, error=False):
        backup.task_lock = None
        backup.save(update_fields=["task_lock"])
        data['backup_task_locks_expired'] += 1
        append_task_console_output(backup, '### WARNING: Backup task expired. This likely means that the backup task has been running for too long and has been marked as failed. Please check the router and the backup task for more details.')
        notify_backup_task_lock_expired(backup)

    for backup in RouterBackup.objects.filter(created__lt=max_backup_task_age, success=False, error=False, task_lock__isnull=True):
        backup.error = True
        backup.error_message = 'Backup task expired'
        backup.save()
        backup.router.routerstatus.last_backup_failed = timezone.now()
        backup.router.routerstatus.save()
        notify_backup_fail(backup)

        if not RouterBackup.objects.filter(router=backup.router, success=False, error=False).exists():
            backup.router.routerstatus.backup_lock = None
            backup.router.routerstatus.save()
        data['backup_tasks_expired'] += 1  # Do not count locks removed for expired tasks

    for router_status in RouterStatus.objects.filter(backup_lock__lt=max_backup_task_age):
        if not RouterBackup.objects.filter(router=router_status.router, success=False, error=False).exists():
            router_status.backup_lock = None
            router_status.last_backup_failed = timezone.now()
            router_status.save()
            data['backup_locks_removed'] += 1

    for router_status in RouterStatus.objects.filter(command_lock__lt=max_command_lock_age):
        router_status.command_lock = None
        router_status.save()
        data['command_locks_removed'] += 1

    for backup_profile in BackupProfile.objects.all():
        if backup_profile.name == 'default':
            backup_list = RouterBackup.objects.filter(Q(router__backup_profile=backup_profile) | Q(router__backup_profile__isnull=True))
        else:
            backup_list = RouterBackup.objects.filter(router__backup_profile=backup_profile)

        if backup_profile.retain_backups_on_error:
            backup_list = backup_list.filter(router__routerstatus__last_backup_failed__isnull=True)

        backup_list.filter(schedule_type='instant', created__lt=timezone.now() - timedelta(days=backup_profile.instant_retention)).delete()
        backup_list.filter(schedule_type='monthly', created__lt=timezone.now() - timedelta(days=backup_profile.monthly_retention)).delete()
        backup_list.filter(schedule_type='weekly', created__lt=timezone.now() - timedelta(days=backup_profile.weekly_retention)).delete()
        backup_list.filter(schedule_type='daily', created__lt=timezone.now() - timedelta(days=backup_profile.daily_retention)).delete()

    expired_messages = Message.objects.filter(created__lt=timezone.now() - timedelta(days=30))
    data['messages_removed'] = expired_messages.count()
    expired_messages.delete()

    return JsonResponse(data)
