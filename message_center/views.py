from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, Http404, get_object_or_404
from django.contrib import messages

from router_manager.models import Router
from user_manager.models import UserAcl
from .forms import MessageSettingsForm, MessageChannelForm
from .models import Notification, MessageChannel, Message, MessageSettings
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .functions import notify_router_status_update, notify_backup_fail, send_notification_message
from backup_data.models import RouterBackup


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
