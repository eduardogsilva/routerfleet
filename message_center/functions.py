import datetime

from router_manager.models import Router
from .models import MessageChannel, Notification, MessageSettings, Message
from backup_data.models import RouterBackup
import requests
from django.utils import timezone


def send_notification_message(message: Message):
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    if message.status != 'pending':
        return
    if message.retry_count > message_settings.max_retry:
        message.status = 'failed'
        message.completed = timezone.now()
        message.save()
        return

    message_response = {'status': 'pending', 'error_message': '', 'error_status_code': 0}
    if message.channel.channel_type == 'callmebot':
        url = f'https://api.callmebot.com/whatsapp.php?phone={message.channel.destination}&text={message.message}&apikey={message.channel.token}'
    elif message.channel.channel_type == 'telegram':
        url = f'https://api.telegram.org/bot{message.channel.token}/sendMessage?chat_id={message.channel.destination}&text={message.message}'
    else:
        message_response['status'] = 'failed'
        message_response['error_message'] = 'Failed to send message: Invalid channel type'
        message_response['error_status_code'] = 0

    if message_response['status'] == 'pending':
        try:
            response = requests.get(url)
            if response.status_code == 200:
                message_response['status'] = 'sent'
            else:
                message_response['status'] = 'failed'
                message_response['error_message'] = response.text
                message_response['error_status_code'] = response.status_code
        except:
            message_response['status'] = 'failed'
            message_response['error_message'] = 'Failed to send message: Request exception'
            message_response['error_status_code'] = 0

    if message_response['status'] == 'sent':
        message.status = 'sent'
        message.completed = timezone.now()
        message.save()
    else:
        message.retry_count += 1
        message.error_message = message_response['error_message']
        message.error_status_code = message_response['error_status_code']
        message.next_retry = timezone.now() + datetime.timedelta(seconds=message_settings.retry_interval)
        message.save()
    return


def notify_router_status_update(router: Router):
    message_channel_list = MessageChannel.objects.filter(enabled=True)
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')

    if message_settings.concatenate_status_change:
        if router.routerstatus.status_online:
            if message_channel_list.filter(status_change_online=True):
                Notification.objects.create(notification_type='status_online', router=router)
        else:
            if message_channel_list.filter(status_change_offline=True):
                Notification.objects.create(notification_type='status_offline', router=router)
    else:
        if router.routerstatus.status_online:
            for message_channel in message_channel_list.filter(status_change_online=True):
                Message.objects.create(
                    channel=message_channel,
                    subject='Router status change: Online',
                    message=f'Router {router.name} ({router.address}) is now online'
                )
        else:
            for message_channel in message_channel_list.filter(status_change_offline=True):
                Message.objects.create(
                    channel=message_channel,
                    subject='Router status change: Offline',
                    message=f'Router {router.name} ({router.address}) is now offline'
                )
    return


def notify_backup_fail(router_backup: RouterBackup):
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    message_channel_list = MessageChannel.objects.filter(enabled=True, backup_fail=True)

    if not message_channel_list:
        return

    if message_settings.concatenate_backup_fails:
        Notification.objects.create(notification_type='backup_fail', router=router_backup.router, router_backup=router_backup)
    else:
        error_message = f'Backup {router_backup.id} failed for router {router_backup.router.name} ({router_backup.router.address})'
        if router_backup.error_message:
            error_message += f'\n\nError message: {router_backup.error_message}'
        for message_channel in message_channel_list:
            Message.objects.create(
                channel=message_channel,
                subject=f'Backup failed: {router_backup.id}',
                message=error_message
            )
    return
