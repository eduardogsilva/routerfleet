import datetime

from router_manager.models import Router
from .models import MessageChannel, Notification, MessageSettings, Message
from backup_data.models import RouterBackup
import requests
from django.utils import timezone


def concatenate_notifications(notification_type: str):
    concatenate_count = 0
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    message_channel_list = MessageChannel.objects.filter(enabled=True)
    if notification_type == 'status_online':
        notification_text = 'Router status change: Online\n'
        notification_list = Notification.objects.filter(notification_type='status_online')
        message_channel_list = message_channel_list.filter(status_change_online=True)
    elif notification_type == 'status_offline':
        notification_text = 'Router status change: Offline\n'
        notification_list = Notification.objects.filter(notification_type='status_offline')
        message_channel_list = message_channel_list.filter(status_change_offline=True)
    elif notification_type == 'backup_fail':
        notification_text = 'Backup failed report\n'
        notification_list = Notification.objects.filter(notification_type='backup_fail')
        message_channel_list = message_channel_list.filter(backup_fail=True)
    else:
        return 0

    notification_list = notification_list.order_by('created')
    for notification in notification_list:
        notification_text_temp = notification_text
        if notification.router_backup:
            notification_text_temp += f'\n- Backup: {notification.router_backup.id} for router {notification.router_backup.router.name} '
        elif notification.router:
            notification_text_temp += f'\n- Router {notification.router.name} ({notification.router.address})'
        if len(notification_text_temp) < message_settings.max_length:
            notification_text = notification_text_temp
            notification.delete()
            concatenate_count += 1
        else:
            break

    for message_channel in message_channel_list:
        Message.objects.create(
            channel=message_channel,
            subject=notification_text.split('\n')[0],
            message=notification_text
        )
    return concatenate_count


def generate_backup_report(data):
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    yesterday = timezone.now() - datetime.timedelta(days=1)
    failed_backup_list = RouterBackup.objects.filter(error=True, updated__gt=yesterday)
    success_backup_list = RouterBackup.objects.filter(success=True, updated__gt=yesterday)
    pending_backup_list = RouterBackup.objects.filter(success=False, error=False, updated__gt=yesterday)
    if data['report_time_exception']:
        message_text = 'Warning: Error calculating report time, please check your timezone settings.\n\n'
    else:
        message_text = ''
    message_text = 'Routerfleet Daily backup report:\n'
    message_text += f'Backups completed: {success_backup_list.count()}\n'
    message_text += f'Backups failed: {failed_backup_list.count()}\n'
    message_text += f'Backups pending: {pending_backup_list.count()}\n'

    if failed_backup_list.count() > 0:
        message_text += '\n=========\n Failed backups:\n'
        message_text_temp = message_text
        truncate_text = 'There are more failed backups, please check the web interface for the full list\n\n'
        for backup in failed_backup_list:
            message_text_temp += f'- Backup {backup.id} for router {backup.router.name} ({backup.router.address})\n'
            if len(message_text_temp + truncate_text) < message_settings.max_length:
                message_text = message_text_temp
            else:
                message_text += truncate_text
                break
    for message_channel in MessageChannel.objects.filter(enabled=True, daily_backup_report=True):
        Message.objects.create(
            channel=message_channel,
            subject='Daily backup report',
            message=message_text
        )
    message_settings.last_daily_backup_report = timezone.now()
    message_settings.save()
    return


def generate_status_report(data):
    message_settings, _ = MessageSettings.objects.get_or_create(name='message_settings')
    router_list = Router.objects.filter(enabled=True, monitoring=True)
    offline_count = router_list.filter(routerstatus__status_online=False).count()
    if data['report_time_exception']:
        message_text = 'Warning: Error calculating report time, please check your timezone settings.\n\n'
    else:
        message_text = ''
    message_text += 'Routerfleet Daily status report:\n'
    message_text += f'Monitored routers: {router_list.count()}\n'
    message_text += f'Online: {router_list.filter(routerstatus__status_online=True).count()}\n'
    message_text += f'Offline: {offline_count}\n'

    if offline_count > 0:
        message_text += '\n=========\n Offline routers:\n'
        message_text_temp = message_text
        truncate_text = 'There are more offline routers, please check the web interface for the full list\n\n'
        for router in router_list.filter(routerstatus__status_online=False):
            message_text_temp += f'- {router.name} ({router.address})\n'
            if len(message_text_temp + truncate_text) < message_settings.max_length:
                message_text = message_text_temp
            else:
                message_text += truncate_text
                break

    message_channel_list = MessageChannel.objects.filter(enabled=True, daily_status_report=True)
    for message_channel in message_channel_list:
        Message.objects.create(
            channel=message_channel,
            subject='Daily status report',
            message=message_text
        )
    message_settings.last_daily_status_report = timezone.now()
    message_settings.save()
    return


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
    
    url = ''
    method = 'GET'
    headers = {}
    data = None

    if message.channel.channel_type == 'callmebot':
        url = f'https://api.callmebot.com/whatsapp.php?phone={message.channel.destination}&text={message.message}&apikey={message.channel.token}'
    elif message.channel.channel_type == 'telegram':
        url = f'https://api.telegram.org/bot{message.channel.token}/sendMessage?chat_id={message.channel.destination}&text={message.message}'
    elif message.channel.channel_type == 'ntfy':
        url = f'https://ntfy.sh/{message.channel.destination}'
        method = 'POST'
        data = message.message.encode('utf-8')
        if message.subject:
             headers = {'Title': message.subject}
    else:
        message_response['status'] = 'failed'
        message_response['error_message'] = 'Failed to send message: Invalid channel type'
        message_response['error_status_code'] = 0

    if message_response['status'] == 'pending':
        try:
            if method == 'GET':
                response = requests.get(url)
            elif method == 'POST':
                response = requests.post(url, data=data, headers=headers)
            
            if response.status_code == 200:
                message_response['status'] = 'sent'
            else:
                message_response['status'] = 'failed'
                message_response['error_message'] = response.text
                message_response['error_status_code'] = response.status_code
        except Exception as e:
            message_response['status'] = 'failed'
            message_response['error_message'] = f'Failed to send message: Request exception {str(e)}'
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
