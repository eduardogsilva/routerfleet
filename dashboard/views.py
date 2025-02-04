from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from backup.models import BackupProfile
from backup_data.models import RouterBackup
from router_manager.models import Router, RouterGroup, RouterStatus, BackupSchedule, SSHKey
from user_manager.models import User
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

import os
import shutil
ALLOWED_DAYS = [3,5,7,10, 15, 30]  # Define allowed values

import os
import shutil
from django.conf import settings

import os
import shutil
from django.conf import settings

def human_readable_size(size):
    """Convert bytes to a human-readable format (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"  # For sizes larger than GB

def get_directory_statistics(directory_path):
    # Get total disk usage
    total, used, free = shutil.disk_usage(directory_path)
    
    # Calculate the size of the directory
    directory_used = sum(os.path.getsize(os.path.join(root, file)) for root, dirs, files in os.walk(directory_path) for file in files)
    
    # Get sizes in a human-readable format
    total_human = human_readable_size(total)
    used_human = human_readable_size(directory_used)
    free_human = human_readable_size(free)

    # Calculate usage percentage
    usage_percentage = (directory_used / total) * 100 if total > 0 else 0

    # Determine storage warning
    storage_warning = ""
    if usage_percentage > 90:
        storage_warning = "Warning: Storage usage is above 90%!"
    elif usage_percentage > 75:
        storage_warning = "Caution: Storage usage is above 75%."

    return {
        "total": total_human,
        "used": used_human,
        "free": free_human,
        "usage_percentage": round(usage_percentage, 2) if total > 0 else 0,
        "storage_warning": storage_warning
    }


@login_required
def view_dashboard(request):
    context = {'page_title': 'Welcome to routerfleet'}
    return render(request, 'dashboard/welcome.html', context=context)


@login_required
def view_status(request):
    settings.MEDIA_ROOT
    context = {
        'page_title': 'Welcome to routerfleet',
        'media_root_stats': get_directory_statistics(settings.MEDIA_ROOT),
        'queue': RouterBackup.objects.filter(success=False, error=False).count(),
        'success_backup_last_24h': RouterBackup.objects.filter(success=True, created__gte=timezone.now() - timedelta(days=1)).count(),
        'error_backup_last_24h': RouterBackup.objects.filter(error=True, created__gte=timezone.now() - timedelta(days=1)).count(),
        'total_router_count':Router.objects.all().count(),
        'router_enabled_count': Router.objects.filter(enabled=True).count(),
        'router_disabled_count': Router.objects.filter(enabled=False).count(),
        'router_online_count': RouterStatus.objects.filter(status_online=True, router__monitoring=True).count(),
        'router_offline_count': RouterStatus.objects.filter(status_online=False, router__monitoring=True).count(),
        'router_not_monitored_count': Router.objects.filter(enabled=True, monitoring=False).count(),
        'routerfleet_version': settings.ROUTERFLEET_VERSION,
    }

    return render(request, 'dashboard/status.html', context=context)
@login_required
def backup_statistics_data(request):
    try:
        days = int(request.GET.get('days', 7))
    except ValueError:
        return HttpResponseBadRequest("Invalid 'days' parameter")

    if days not in ALLOWED_DAYS:
        return HttpResponseBadRequest("Invalid 'days' parameter")
    today = timezone.now()
    start_date = today - timedelta(days=days)

    dates = [start_date + timedelta(days=i) for i in range(days + 1)]
    success_data = []
    error_data = []

    for i in range(days):
        day_start = dates[i]
        day_end = dates[i + 1]
        success_count = RouterBackup.objects.filter(created__gte=day_start, created__lt=day_end, success=True).count()
        error_count = RouterBackup.objects.filter(created__gte=day_start, created__lt=day_end, error=True).count()
        success_data.append(success_count)
        error_data.append(error_count)

    data = {
        'dates': [date.strftime('%Y-%m-%d') for date in dates[:-1]],
        'success_data': success_data,
        'error_data': error_data,
    }
    return JsonResponse(data)

@login_required
def router_status_data(request):
    try:
        days = int(request.GET.get('days', '7'))
        
    except ValueError:
        return HttpResponseBadRequest(f"Invalid 'days' {days} parameter")

    if days not in ALLOWED_DAYS:
        return HttpResponseBadRequest("Invalid 'days' parameter. Must be one of: " + ', '.join(map(str, ALLOWED_DAYS)))

    today = timezone.now()
    start_date = today - timedelta(days=days)

    # Create a list of dates for the period
    dates = [start_date + timedelta(days=i) for i in range(days + 1)]
    router_statuses = RouterStatus.objects.filter(router__enabled=True)

    online_data = []
    offline_data = []

    for i in range(days):
        day_start = dates[i]
        day_end = dates[i + 1]

        # Get statuses that changed within the current day
        daily_statuses = router_statuses.filter(last_status_change__gte=day_start, last_status_change__lt=day_end)
        
        online_count = daily_statuses.filter(status_online=True).count()
        offline_count = daily_statuses.filter(status_online=False).count()

        # Get routers that have not changed status on the current day
        unchanged_routers = router_statuses.exclude(last_status_change__gte=day_start, last_status_change__lt=day_end)

        for router_status in unchanged_routers:
            last_change = router_status.last_status_change
            # Only perform the comparison if last_change is not None
            if last_change and last_change < day_start:
                if router_status.status_online:
                    online_count += 1
                else:
                    offline_count += 1

        online_data.append(online_count)
        offline_data.append(offline_count)

    data = {
        'dates': [date.strftime('%Y-%m-%d') for date in dates[:-1]],
        'online_data': online_data,
        'offline_data': offline_data,
    }

    return JsonResponse(data)