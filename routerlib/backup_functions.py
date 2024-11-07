import datetime
from django.utils import timezone
from backup_data.models import RouterBackup
import os
from scp import SCPClient
from django.core.files.base import ContentFile

from message_center.functions import notify_backup_fail
from routerlib.functions import gen_backup_name, connect_to_ssh, get_router_backup_file_extension


def perform_backup(router_backup: RouterBackup):
    if router_backup.success or router_backup.error:
        router_backup.router.routerstatus.backup_lock = None
        router_backup.router.routerstatus.save()
        return
    if not router_backup.router.backup_profile:
        router_backup.error = True
        router_backup.error_message = "No backup profile assigned"
        router_backup.save()
        router_backup.router.routerstatus.backup_lock = None
        router_backup.router.routerstatus.save()
        notify_backup_fail(router_backup)
        return
    if router_backup.retry_count > router_backup.router.backup_profile.max_retry:
        router_backup.error = True
        router_backup.save()
        router_backup.router.routerstatus.backup_lock = None
        router_backup.router.routerstatus.save()
        notify_backup_fail(router_backup)
        return

    if router_backup.backup_pending_retrieval:
        backup_success, error_message = retrieve_backup(router_backup)
        if error_message:
            handle_backup_failure(router_backup, error_message)
            return

        if backup_success:
            clean_up_backup_files(router_backup)
            if router_backup.schedule_time:
                start_time = router_backup.schedule_time
            else:
                start_time = router_backup.created
            router_backup.queue_length = (timezone.now() - start_time).seconds
            router_backup.finish_time = timezone.now()
            router_backup.backup_pending_retrieval = False
            router_backup.error_message = ''
            router_backup.success = True
            router_backup.save()
            router_backup.router.routerstatus.last_backup = timezone.now()
            router_backup.router.routerstatus.last_backup_failed = None
            router_backup.router.routerstatus.backup_lock = None
            router_backup.router.routerstatus.save()
        else:
            handle_backup_failure(router_backup, error_message)
    else:
        backup_success, backup_files, error_message = execute_backup(router_backup)
        if backup_success:
            router_backup.backup_pending_retrieval = True
            router_backup.error_message = ''
            router_backup.retry_count = 0
            router_backup.next_retry = timezone.now() + datetime.timedelta(seconds=router_backup.router.backup_profile.retrieve_interval)
            router_backup.save()
        else:
            handle_backup_failure(router_backup, error_message)
    return


def handle_backup_failure(router_backup: RouterBackup, error_message):
    router_backup.error_message = error_message
    router_backup.retry_count += 1
    router_backup.next_retry = timezone.now() + datetime.timedelta(minutes=router_backup.router.backup_profile.retry_interval)
    router_backup.save()


def execute_backup(router_backup: RouterBackup):
    error_message = ""
    router = router_backup.router
    backup_name = gen_backup_name(router_backup)
    file_extension = get_router_backup_file_extension(router.router_type)
    ssh_client = None
    additional_parameters = ""
    try:
        if router_backup.router.router_type == 'routeros':
            if router.backup_profile:
                if router.backup_profile.parameter_sensitive:
                    additional_parameters += ' show-sensitive'
                if router.backup_profile.parameter_terse:
                    additional_parameters += ' terse'

            ssh_client = connect_to_ssh(router.address, router.port, router.username, router.password, router.ssh_key)
            ssh_client.exec_command(f'/system backup save name={backup_name}.{file_extension["binary"]}')
            ssh_client.exec_command(f'/export file={backup_name}.{file_extension["text"]} {additional_parameters}')
            return True, [f'{backup_name}.{file_extension["binary"]}', f'{backup_name}.{file_extension["text"]}'], error_message
        elif router_backup.router.router_type == 'openwrt':
            ssh_client = connect_to_ssh(router.address, router.port, router.username, router.password, router.ssh_key)
            stdin, stdout, stderr = ssh_client.exec_command('uci export')
            backup_text = stdout.read().decode('utf-8')
            if backup_text:
                router_backup.backup_text = backup_text
                router_backup.backup_text_filename = f'{backup_name}.{file_extension["text"]}'
                router_backup.save()
            else:
                return False, [], "Failed to execute backup: Empty backup text"
            ssh_client.exec_command(f'sysupgrade --create-backup /tmp/{backup_name}.{file_extension["binary"]}')
            return True, [f'/tmp/{backup_name}.{file_extension["binary"]}', f'{backup_name}.{file_extension["text"]}'], error_message
        else:
            error_message = f"Router type not supported: {router_backup.router.get_router_type_display()}"
            return False, [], error_message
    except Exception as e:
        error_message = f"Failed to execute backup: {str(e)}"
        return False, [], error_message
    finally:
        if ssh_client:
            ssh_client.close()


def retrieve_backup(router_backup: RouterBackup):
    error_message = ""
    router = router_backup.router
    backup_name = gen_backup_name(router_backup)
    success = False
    file_extension = get_router_backup_file_extension(router.router_type)
    ssh_client = None

    try:
        if router_backup.router.router_type == 'routeros':
            rsc_file_path = f'/tmp/{backup_name}.{file_extension["text"]}'
            backup_file_path = f'/tmp/{backup_name}.{file_extension["binary"]}'
            ssh_client = connect_to_ssh(router.address, router.port, router.username, router.password, router.ssh_key)
            scp_client = SCPClient(ssh_client.get_transport())
            scp_client.get(f'/{backup_name}.{file_extension["text"]}', rsc_file_path)
            scp_client.get(f'/{backup_name}.{file_extension["binary"]}', backup_file_path)

            with open(rsc_file_path, 'r') as rsc_file:
                rsc_content = rsc_file.read()
                rsc_content_cleaned = '\n'.join(
                    line for line in rsc_content.split('\n') if not line.strip().startswith('#'))
                router_backup.backup_text = rsc_content_cleaned
                router_backup.backup_text_filename = f'{backup_name}.{file_extension["text"]}'

            with open(backup_file_path, 'rb') as backup_file:
                router_backup.backup_binary.save(f"{backup_name}.{file_extension['binary']}", ContentFile(backup_file.read()))

            router_backup.save()
            os.remove(rsc_file_path)
            os.remove(backup_file_path)
            ssh_client.exec_command(f'/file remove "{backup_name}.{file_extension["text"]}"')
            ssh_client.exec_command(f'/file remove "{backup_name}.{file_extension["binary"]}"')
            success = True

        elif router_backup.router.router_type == 'openwrt':
            remote_backup_file_path = f'/tmp/{backup_name}.{file_extension["binary"]}'
            local_backup_file_path = f'/tmp/{backup_name}.{file_extension["binary"]}'
            ssh_client = connect_to_ssh(router.address, router.port, router.username, router.password, router.ssh_key)
            scp_client = SCPClient(ssh_client.get_transport())
            scp_client.get(remote_backup_file_path, local_backup_file_path)
            with open(local_backup_file_path, 'rb') as backup_file:
                router_backup.backup_binary.save(f"{backup_name}.{file_extension['binary']}", ContentFile(backup_file.read()))
            router_backup.save()
            os.remove(local_backup_file_path)
            ssh_client.exec_command(f'rm {remote_backup_file_path}')
            success = True

        else:
            error_message = f"Router type not supported: {router_backup.router.get_router_type_display()}"
            return success, error_message

    except Exception as e:
        return success, f"Failed to retrieve backup files: {str(e)}"
    finally:
        if ssh_client:
            ssh_client.close()

    return success, error_message


def clean_up_backup_files(router_backup: RouterBackup):
    router = router_backup.router
    ssh_client = None
    try:
        if router_backup.router.router_type == 'routeros':
            ssh_client = connect_to_ssh(router.address, router.port, router.username, router.password, router.ssh_key)
            ssh_client.exec_command('file remove [find where name~"routerfleet-backup-"]')
        elif router_backup.router.router_type == 'openwrt':
            ssh_client = connect_to_ssh(router.address, router.port, router.username, router.password, router.ssh_key)
            ssh_client.exec_command('rm /tmp/routerfleet-backup-*')
        else:
            print(f"Router type not supported: {router_backup.router.get_router_type_display()}")
    except Exception as e:
        print(f"Failed to clean up backup files: {str(e)}")
    finally:
        if ssh_client:
            ssh_client.close()
