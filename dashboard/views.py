from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from backup.models import BackupProfile
from backup_data.models import RouterBackup
from router_manager.models import Router, RouterGroup, RouterStatus, BackupSchedule, SSHKey
from integration_manager.models import ExternalIntegration
from user_manager.models import User
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

import os
import shutil


def get_directory_statistics(directory_path):
    total, used, free = shutil.disk_usage(directory_path)
    # Convert to GB
    total = total // (2 ** 30)
    used = used // (2 ** 30)
    free = free // (2 ** 30)
    usage_percentage = (used / total) * 100

    return {
        "total_gb": total,
        "used_gb": used,
        "free_gb": free,
        "usage_percentage": round(usage_percentage, 2)
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
        'router_count': Router.objects.filter(enabled=True).count(),
        'router_online_count': RouterStatus.objects.filter(status_online=True, router__monitoring=True).count(),
        'router_offline_count': RouterStatus.objects.filter(status_online=False, router__monitoring=True).count(),
        'router_not_monitored_count': Router.objects.filter(enabled=True, monitoring=False).count(),
        'routerfleet_version': settings.ROUTERFLEET_VERSION,
    }

    return render(request, 'dashboard/status.html', context=context)
