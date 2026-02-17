import json
import datetime
import re
from django.utils import timezone
from router_manager.models import RouterInformation, Router
from routerlib.functions import connect_to_ssh


def _parse_routeros_key_value_output(output: str) -> dict:
    """
    Parse lines like "key:    value" into a dict.
    Skip blank lines or lines starting with '[' (the prompt).
    """
    data = {}
    # Normalize and split
    for raw_line in output.replace('\r', '').splitlines():
        line = raw_line.strip()
        # skip empty or prompt lines
        if not line or line.startswith('['):
            continue
        if ':' not in line:
            continue
        key, val = line.split(':', 1)
        data[key.strip()] = val.strip()
    return data


def get_router_information(router_information: RouterInformation):
    """
    Connect to the router, retrieve info, and store it in RouterInformation.
    """
    router = router_information.router
    field_max_length = 100
    success = False
    error_message = ''

    try:
        ssh = connect_to_ssh(router.address, router.port, router.username, router.password, router.ssh_key)
        json_data = {}

        if router.router_type in ('routeros', 'routeros-branded'):
            for cmd in ['/system resource print', '/system routerboard print']:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                raw = stdout.read().decode('utf-8', errors='ignore')
                parsed = _parse_routeros_key_value_output(raw)
                json_data[cmd] = parsed

            rb = json_data['/system routerboard print']
            sr = json_data['/system resource print']

            if sr:
                router_information.model_name = sr.get('board-name', '')[:field_max_length]
                router_information.os_version = sr.get('version', '')[:field_max_length]
                router_information.architecture = sr.get('architecture-name', '')[:field_max_length]
                router_information.cpu = sr.get('cpu', '')[:field_max_length]
                success = True
            if rb:
                router_information.model_version = rb.get('model', '')[:field_max_length]
                router_information.serial_number = rb.get('serial-number', '')[:field_max_length]
                router_information.firmware_version = rb.get('current-firmware', '')[:field_max_length]
                success = True
            if not success:
                return False, 'Failed to retrieve router information'

        elif router.router_type == 'openwrt':
            stdin, stdout, stderr = ssh.exec_command('cat /etc/os-release')
            osrel = {}
            for line in stdout.read().decode('utf-8').splitlines():
                if '=' in line:
                    k, v = line.split('=', 1)
                    osrel[k] = v.strip().strip('"')
            json_data['cat /etc/os-release'] = osrel

            # hostname
            stdin, stdout, stderr = ssh.exec_command('uci get system.@system[0].hostname')
            hostname = stdout.read().decode('utf-8').strip()
            json_data['uci get system.@system[0].hostname'] = hostname

            # architecture
            stdin, stdout, stderr = ssh.exec_command('uname -m')
            arch = stdout.read().decode('utf-8').strip()
            json_data['uname -m'] = arch

            # fallback serial (MAC of eth0)
            stdin, stdout, stderr = ssh.exec_command('cat /sys/class/net/eth0/address')
            mac = stdout.read().decode('utf-8').strip()
            json_data['cat /sys/class/net/eth0/address'] = mac

            if osrel:
                router_information.model_name       = osrel.get('OPENWRT_DEVICE_MODEL', '')[:field_max_length]
                router_information.model_version    = osrel.get('VERSION_ID', '')[:field_max_length]
                router_information.serial_number    = mac[:field_max_length]
                router_information.os_version       = osrel.get('VERSION', '')[:field_max_length]
                router_information.firmware_version = osrel.get('OPENWRT_RELEASE', '')[:field_max_length]
                router_information.architecture     = arch[:field_max_length]
                success = True
            if not success:
                return False, 'Failed to retrieve router information'

        elif router.router_type == 'ubiquiti-airos':
            stdin, stdout, stderr = ssh.exec_command('cat /etc/version')
            version_raw = stdout.read().decode('utf-8', errors='ignore').strip()
            json_data['cat /etc/version'] = version_raw
            stdin, stdout, stderr = ssh.exec_command('cat /etc/board.info')
            board_raw = stdout.read().decode('utf-8', errors='ignore')
            json_data['cat /etc/board.info'] = board_raw
            board = {}
            for line in board_raw.splitlines():
                line = line.strip()
                if not line or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                board[k.strip()] = v.strip()
            if not board:
                return False, 'Failed to retrieve router information from /etc/board.info'

            stdin, stdout, stderr = ssh.exec_command('uname -r')
            kernel_version = stdout.read().decode('utf-8', errors='ignore').strip()
            json_data['uname -r'] = kernel_version

            stdin, stdout, stderr = ssh.exec_command('cat /proc/cpuinfo')
            cpuinfo_raw = stdout.read().decode('utf-8', errors='ignore')
            json_data['cat /proc/cpuinfo'] = cpuinfo_raw
            cpuinfo = {}

            for line in cpuinfo_raw.splitlines():
                if ':' not in line:
                    continue
                k, v = line.split(':', 1)
                cpuinfo[k.strip().lower()] = v.strip()

            router_information.model_name = board.get('board.name', '')[:field_max_length]
            router_information.model_version = (
                    board.get('board.model', '') or board.get('board.shortname', '')
            )[:field_max_length]

            router_information.serial_number = (
                    board.get('board.device_id', '') or board.get('board.hwaddr', '')
            )[:field_max_length]
            router_information.firmware_version = version_raw[:field_max_length]
            router_information.os_version = kernel_version[:field_max_length]
            cpu_model = cpuinfo.get('cpu model', '')
            router_information.architecture = (
                cpu_model.split()[0] if cpu_model else ''
            )[:field_max_length]
            router_information.cpu = (
                    cpuinfo.get('system type', '')
                    or cpu_model
                    or board.get('board.cpurevision', '')
            )[:field_max_length]
            success = True
        else:
            return False, f"Router type not supported: {router.get_router_type_display()}"

        if success:
            router_information.success        = True
            router_information.error          = False
            router_information.retry_count    = 0
            router_information.next_retry     = None
            router_information.error_message = ''
            router_information.last_retrieval = timezone.now()
            router_information.json_data = json.dumps(json_data)
            router_information.save()

    except Exception as e:
        success = False
        error_message = str(e)

    finally:
        try:
            ssh.close()
        except:
            pass

    return success, error_message


def update_router_information(router_information: RouterInformation):
    max_retry = 3
    retry_minutes = 5

    success = False
    error_message = ''

    if router_information.retry_count > max_retry:
        router_information.error = True
        router_information.success = False
        router_information.next_retry = None
        router_information.retry_count = 0
        router_information.last_retrieval = timezone.now()
        if router_information.error_message:
            router_information.error_message += f"\nMax retries reached for {router_information.router.name}"
        else:
            router_information.error_message = f"Max retries reached for {router_information.router.name}"
        router_information.save()
        return False, router_information.error_message
    try:
        success, error_message = get_router_information(router_information)
    except Exception as e:
        success = False
        error_message = f"Failed to update router information for {router_information.router.name}. Exception: {e}"

    if not success:
        router_information.error = True
        router_information.success = False
        router_information.next_retry = timezone.now() + datetime.timedelta(minutes=retry_minutes)
        router_information.retry_count += 1
        router_information.last_retrieval = timezone.now()
        if error_message:
            router_information.error_message = error_message
        else:
            router_information.error_message = f"Failed to update router information for {router_information.router.name}"
        router_information.save()

    return success, error_message
