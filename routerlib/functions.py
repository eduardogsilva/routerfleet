import paramiko
import telnetlib


def get_router_features(router_type):
    if router_type in ['openwrt', 'routeros']:
        return ['backup', 'reverse_monitoring', 'ssh', 'ssh_key']
    else:
        return []


def get_router_backup_file_extension(router_type):
    if router_type == 'routeros':
        return {'text': 'rsc', 'binary': 'backup'}
    else:
        return {'text': 'txt', 'binary': 'bin'}


def gen_backup_name(router_backup):
    return f'routerfleet-backup-{router_backup.id}-{router_backup.schedule_type}-{router_backup.router.address}-{router_backup.created.strftime("%Y-%m-%d_%H-%M")}'


def test_authentication(router_type, address, username, password, sshkey=None):
    router_features = get_router_features(router_type)
    if 'ssh' in router_features:
        connection_type = 'ssh'
    elif 'telnet' in router_features:
        connection_type = 'telnet'
    else:
        return False, 'Router type not supported'

    if connection_type == 'ssh':
        return test_ssh_authentication(router_type, address, username, password, sshkey)
    elif connection_type == 'telnet':
        return test_telnet_authentication(address, username, password, sshkey=None)


def test_ssh_authentication(router_type, address, username, password, sshkey=None):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(address, username=username, password=password, look_for_keys=False, timeout=10, allow_agent=False)

        if router_type == 'routeros':
            stdin, stdout, stderr = ssh.exec_command('/system resource print')
            output = stdout.read().decode()
            if 'platform: MikroTik' in output:
                result = True, 'Success: MikroTik device confirmed'
            else:
                result = False, 'Device is not MikroTik'
        elif router_type == 'openwrt':
            stdin, stdout, stderr = ssh.exec_command('ubus call system board')
            output = stdout.read().decode()
            if 'OpenWrt' in output:
                result = True, 'Success: OpenWRT device confirmed'
            else:
                result = False, 'Device is not OpenWRT'
        else:
            result = False, 'Unsupported device type'

        ssh.close()
        return result
    except Exception as e:
        return False, str(e)


def test_telnet_authentication(address, username, password, sshkey=None):
    try:
        tn = telnetlib.Telnet(address)
        tn.read_until(b"login: ")
        tn.write(username.encode('ascii') + b"\n")
        tn.read_until(b"Password: ")
        tn.write(password.encode('ascii') + b"\n")
        tn.write(b"exit\n")
        tn.close()
        return True, 'Success'
    except Exception as e:
        print(f"Telnet connection failed: {e}")
        return False, str(e)
