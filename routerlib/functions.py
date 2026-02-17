from io import StringIO

import re
import paramiko
import telnetlib


def get_router_features(router_type):
    if router_type in ['openwrt', 'routeros', 'routeros-branded', 'ubiquiti-airos']:
        return ['backup', 'reverse_monitoring', 'ssh', 'ssh_key']
    else:
        return []


def get_router_backup_file_extension(router_type):
    if router_type == 'routeros' or router_type == 'routeros-branded':
        return {'text': 'rsc', 'binary': 'backup'}
    elif router_type == 'openwrt':
        return {'text': 'txt', 'binary': 'tar.gz'}
    else:
        return {'text': 'txt', 'binary': 'bin'}


def gen_backup_name(router_backup):
    return f'routerfleet-backup-{router_backup.id}-{router_backup.schedule_type}-{router_backup.created.strftime("%Y-%m-%d_%H-%M")}'


def load_private_key_from_string(key_str):
    key_types = [
        paramiko.RSAKey,
        paramiko.ECDSAKey,
        paramiko.Ed25519Key,
    ]
    for key_type in key_types:
        try:
            key_file_obj = StringIO(key_str)
            return key_type.from_private_key(key_file_obj)
        except paramiko.ssh_exception.SSHException:
            continue
    return None


def connect_to_ssh(address, port, username, password, sshkey=None):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if sshkey:
        private_key = load_private_key_from_string(sshkey.private_key)
        ssh_client.connect(address, port=port, username=username, pkey=private_key, look_for_keys=False, timeout=10, allow_agent=False)
    else:
        ssh_client.connect(address, port=port, username=username, password=password, look_for_keys=False, timeout=10, allow_agent=False)
    return ssh_client


def test_authentication(router_type, address, port, username, password, sshkey=None):
    router_features = get_router_features(router_type)
    if 'ssh' in router_features:
        connection_type = 'ssh'
    elif 'telnet' in router_features:
        connection_type = 'telnet'
    else:
        return False, 'Router type not supported'

    if connection_type == 'ssh':
        return test_ssh_authentication(router_type, address, port, username, password, sshkey)
    elif connection_type == 'telnet':
        return test_telnet_authentication(address, username, password, sshkey=None)


def test_ssh_authentication(router_type, address, port, username, password, sshkey=None):
    try:
        ssh_client = connect_to_ssh(address, port, username, password, sshkey)
        if router_type == 'routeros' or router_type == 'routeros-branded':
            stdin, stdout, stderr = ssh_client.exec_command('/system resource print')
            output = stdout.read().decode()
            if router_type == 'routeros':
                if 'platform: MikroTik' in output:
                    result = True, 'Success: MikroTik device confirmed'
                else:
                    result = False, 'Device is not MikroTik'
            else:
                if 'platform: MikroTik' in output:
                    result = False, 'Device is not branded. Please select Mikrotik (RouterOS)'
                elif 'platform: ' in output:
                    result = True, 'Success: MikroTik branded device confirmed'
                else:
                    result = False, 'Device is not MikroTik'

        elif router_type == 'openwrt':
            stdin, stdout, stderr = ssh_client.exec_command('ubus call system board')
            output = stdout.read().decode()
            if 'OpenWrt' in output:
                result = True, 'Success: OpenWRT device confirmed'
            else:
                result = False, 'Device is not OpenWRT'

        elif router_type == 'ubiquiti-airos':
            stdin, stdout, stderr = ssh_client.exec_command('cat /etc/version')
            output = stdout.read().decode().strip()
            if re.match(r'^[A-Z]{2}\.v\d.*$', output):
                result = True, f'Success: Ubiquiti airOS device confirmed ({output})'
            else:
                result = False, 'Device is not airOS'

        else:
            result = False, 'Unsupported device type'

        ssh_client.close()
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
