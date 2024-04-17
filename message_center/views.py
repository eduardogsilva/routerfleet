from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, Http404, get_object_or_404
from django.contrib import messages
import pytz
from router_manager.models import Router
from routerfleet_tools.models import WebadminSettings
from user_manager.models import UserAcl
from .forms import MessageSettingsForm, MessageChannelForm
from .models import Notification, MessageChannel, Message, MessageSettings
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .functions import notify_router_status_update, notify_backup_fail, send_notification_message, \
    concatenate_notifications, generate_backup_report, generate_status_report
from backup_data.models import RouterBackup
import datetime
from django.utils import timezone


@login_required()
def view_debug_test_messages(request):
    if not settings.DEBUG:
        raise Http404
    data = {'status': 'success'}
    router = None
    router_backup = None
    if request.GET.get('router_uuid'):
        router = get_object_or_404(Router, uuid=request.GET.get('router_uuid'))
        print(f'Creating test message for router {router.name}')
        notify_router_status_update(router)
    elif request.GET.get('backup_id'):
        router_backup = get_object_or_404(RouterBackup, id=request.GET.get('backup_id'))
        notify_backup_fail(router_backup)
    else:
        for message in Message.objects.filter(status='pending'):
            send_notification_message(message)
    return JsonResponse(data)


def view_cron_daily_reports(request):
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    now = timezone.now()
    data = {
        'status': 'success', 'valid_report_window': False, 'next_report_time': None,
        'report_time_exception': False, 'no_channel_available': '',
        'run_backup_report': False, 'run_status_report': False,
    }
    last_report_limit = now - datetime.timedelta(hours=12)

    try:
        report_hour, report_minute = map(int, message_settings.daily_report_time.split(':'))
        if not 0 <= report_hour <= 23:
            report_hour = 0
        if not 0 <= report_minute <= 59:
            report_minute = 0
        user_timezone = pytz.timezone(settings.TIME_ZONE)
        local_now = now.astimezone(user_timezone)
        report_time = local_now.replace(hour=report_hour, minute=report_minute, second=0, microsecond=0)
    except:
        report_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        data['report_time_exception'] = True

    if report_time < now - datetime.timedelta(hours=2):
        report_time = report_time + datetime.timedelta(days=1)
    data['next_report_time'] = report_time.isoformat()
    report_time_window_start = report_time - datetime.timedelta(hours=1)
    report_time_window_end = report_time + datetime.timedelta(hours=1)

    if now < report_time:
        data['status'] = 'waiting for backup time'
        return JsonResponse(data)

    if report_time_window_start < now < report_time_window_end:
        data['valid_report_window'] = True
    else:
        return JsonResponse(data)

    run_backup_report = False
    run_status_report = False
    if message_settings.last_daily_backup_report:
        if message_settings.last_daily_backup_report < last_report_limit:
            run_backup_report = True
    else:
        run_backup_report = True
    if message_settings.last_daily_status_report:
        if message_settings.last_daily_status_report < last_report_limit:
            run_status_report = True
    else:
        run_status_report = True

    data['run_backup_report'] = run_backup_report
    data['run_status_report'] = run_status_report

    # Run only one report at a time
    if run_backup_report:
        if MessageChannel.objects.filter(enabled=True, daily_backup_report=True):
            generate_backup_report(data)
        else:
            data['run_backup_report'] = False
            data['no_channel_available'] = 'backup_report '
    elif run_status_report:
        if MessageChannel.objects.filter(enabled=True, daily_status_report=True):
            generate_status_report(data)
        else:
            data['run_status_report'] = False
            data['no_channel_available'] += 'status_report'

    return JsonResponse(data)


def view_cron_send_messages(request):
    data = {
        'status': 'success',
        'messages_sent': 0,
    }
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    webadmin_settings, _ = WebadminSettings.objects.get_or_create(name='webadmin_settings')
    update_notification = ''
    if webadmin_settings.update_available:
        update_notification = '\n\nA new version of RouterFleet is available. Please update your installation to get the latest security and feature updates.'
    message_list = Message.objects.filter(status='pending', next_retry__isnull=True)

    if not message_list:
        message_list = Message.objects.filter(status='pending', next_retry__lte=timezone.now())

    for message in message_list:
        if update_notification and message.retry_count == 0:
            if len(message.message + update_notification) < message_settings.max_length:
                message.message += update_notification
                message.save()
        send_notification_message(message)
        data['messages_sent'] += 1
    return JsonResponse(data)


def view_cron_concatenate_notifications(request):
    data = {
        'status': 'success',
        'notification_type': {
            'status_online': 0,
            'status_offline': 0,
            'backup_fail': 0,
        }
    }
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    status_change_limit = timezone.now() - datetime.timedelta(seconds=message_settings.status_change_delay)
    backup_fail_limit = timezone.now() - datetime.timedelta(seconds=message_settings.backup_fails_delay)

    if Notification.objects.filter(created__lte=status_change_limit, notification_type='status_online').exists():
        data['notification_type']['status_online'] = concatenate_notifications('status_online')
    if Notification.objects.filter(created__lte=status_change_limit, notification_type='status_offline').exists():
        data['notification_type']['status_offline'] = concatenate_notifications('status_offline')
    if Notification.objects.filter(created__lte=backup_fail_limit, notification_type='backup_fail').exists():
        data['notification_type']['backup_fail'] = concatenate_notifications('backup_fail')
    return JsonResponse(data)


@login_required()
def view_message_channel_list(request):
    if not UserAcl.objects.filter(user=request.user).filter(user_level__gte=20).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    message_channels = MessageChannel.objects.all()
    context = {
        'message_settings': message_settings,
        'message_channels': message_channels,
    }
    return render(request, 'message_center/message_channel_list.html', context=context)


@login_required()
def view_manage_message_settings(request):
    if not UserAcl.objects.filter(user=request.user).filter(user_level__gte=40).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    form = MessageSettingsForm(request.POST or None, instance=message_settings)
    if form.is_valid():
        form.save()
        messages.success(request, 'Message Settings saved successfully')
        return redirect('/message_center/channel_list/')
    context = {
        'message_settings': message_settings,
        'form': form,
    }
    return render(request, 'generic_form.html', context=context)


@login_required()
def view_manage_message_channel(request):
    if not UserAcl.objects.filter(user=request.user).filter(user_level__gte=40).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    if request.GET.get('uuid'):
        message_channel = MessageChannel.objects.get(uuid=request.GET.get('uuid'))
        if request.GET.get('action') == 'delete':
            if request.GET.get('confirmation') == 'delete':
                message_channel.delete()
                messages.success(request, 'Message Channel deleted successfully')
                return redirect('/message_center/channel_list/')
            else:
                messages.warning(request, 'Message Channel not deleted|Invalid confirmation')
                return redirect('/message_center/channel_list/')
    else:
        message_channel = None

    form = MessageChannelForm(request.POST or None, instance=message_channel)
    if form.is_valid():
        form.save()
        messages.success(request, 'Message Channel saved successfully')
        return redirect('/message_center/channel_list/')
    context = {
        'message_settings': message_settings,
        'form': form,
    }
    return render(request, 'generic_form.html', context=context)
