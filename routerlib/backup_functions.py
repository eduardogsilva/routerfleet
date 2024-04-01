import datetime
from django.utils import timezone
from backup_data.models import RouterBackup
import paramiko
import os
from scp import SCPClient
from django.core.files.base import ContentFile
from routerlib.functions import gen_backup_name


def perform_backup(router_backup: RouterBackup):
    if router_backup.success or router_backup.error:
        return
    if not router_backup.router.backup_profile:
        router_backup.error = True
        router_backup.error_message = "No backup profile assigned"
        router_backup.save()
        return
    if router_backup.retry_count > router_backup.router.backup_profile.max_retry:
        router_backup.error = True
        router_backup.save()
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
        else:
            handle_backup_failure(router_backup, error_message)
    else:
        backup_success, backup_files, error_message = execute_backup(router_backup)
        if backup_success:
            router_backup.backup_pending_retrieval = True
            router_backup.error_message = ''
            router_backup.retry_count = 0
            router_backup.next_retry = timezone.now() + datetime.timedelta(minutes=router_backup.router.backup_profile.backup_interval)
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
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if router_backup.router.router_type == 'routeros':
            ssh_client.connect(
                router_backup.router.address, username=router_backup.router.username,
                password=router_backup.router.password, look_for_keys=False, allow_agent=False, timeout=10
            )
            backup_name = gen_backup_name(router_backup)
            ssh_client.exec_command(f'/system backup save name={backup_name}.backup')
            ssh_client.exec_command(f'/export file={backup_name}.rsc')
            return True, [f"{backup_name}.backup", f"{backup_name}.rsc"], error_message
        else:
            error_message = f"Router type not supported: {router_backup.router.get_router_type_display()}"
            return False, [], error_message
    except Exception as e:
        error_message = f"Failed to execute backup: {str(e)}"
        return False, [], error_message
    finally:
        ssh_client.close()


def retrieve_backup(router_backup: RouterBackup):
    error_message = ""
    backup_name = gen_backup_name(router_backup)

    success = False
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if router_backup.router.router_type == 'routeros':
            rsc_file_path = f"/tmp/{backup_name}.rsc"
            backup_file_path = f"/tmp/{backup_name}.backup"

            ssh_client.connect(router_backup.router.address, username=router_backup.router.username,
                               password=router_backup.router.password, look_for_keys=False, allow_agent=False,
                               timeout=10)
            scp_client = SCPClient(ssh_client.get_transport())

            scp_client.get(f"/{backup_name}.rsc", rsc_file_path)
            scp_client.get(f"/{backup_name}.backup", backup_file_path)

            with open(rsc_file_path, 'r') as rsc_file:
                rsc_content = rsc_file.read()
                rsc_content_cleaned = '\n'.join(
                    line for line in rsc_content.split('\n') if not line.strip().startswith('#'))
                router_backup.backup_text = rsc_content_cleaned
                router_backup.backup_text_filename = f"{backup_name}.rsc"

            with open(backup_file_path, 'rb') as backup_file:
                router_backup.backup_binary.save(f"{backup_name}.backup", ContentFile(backup_file.read()))

            router_backup.save()
            os.remove(rsc_file_path)
            os.remove(backup_file_path)
            ssh_client.exec_command(f'/file remove "{backup_name}.rsc"')
            ssh_client.exec_command(f'/file remove "{backup_name}.backup"')
            success = True
        else:
            error_message = f"Router type not supported: {router_backup.router.get_router_type_display()}"
            return success, error_message

    except Exception as e:
        return success, f"Failed to retrieve backup files: {str(e)}"
    finally:
        ssh_client.close()

    return success, error_message


def clean_up_backup_files(router_backup: RouterBackup):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if router_backup.router.router_type == 'routeros':
            ssh_client.connect(
                router_backup.router.address, username=router_backup.router.username,
                password=router_backup.router.password, look_for_keys=False, timeout=10, allow_agent=False
            )
            ssh_client.exec_command('file remove [find where name~"routerfleet-backup-"]')
        else:
            print(f"Router type not supported: {router_backup.router.get_router_type_display()}")
    except Exception as e:
        print(f"Failed to clean up backup files: {str(e)}")
    finally:
        ssh_client.close()
