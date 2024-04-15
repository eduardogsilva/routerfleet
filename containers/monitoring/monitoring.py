import requests
import time
from datetime import datetime
from subprocess import Popen, PIPE
import os
import uuid


DEBUG = False
API_ADDRESS = "http://routerfleet:8001"

HOST_LIST_URL = f"{API_ADDRESS}/monitoring/export_router_list/"
UPDATE_STATUS_URL = f"{API_ADDRESS}/monitoring/update_router_status/"
CONFIG_TIMESTAMP_URL = f"{API_ADDRESS}/monitoring/router_config_timestamp/"
UPDATE_HOST_LIST_INTERVAL = 600  # How often to update the router list in seconds
MONITOR_INTERVAL = 60  # How often to monitor each router in seconds
MAX_NOTIFICATIONS_PER_MONITOR_INTERVAL = 50  # Throttle the number of notifications sent to the remote API


# Global variables
host_list = []
host_list_update_timestamp = 0
notification_count = 0
current_router_config_timestamp = ''
remote_router_config_timestamp = ''
api_key = ''


def get_verbose_status(status):
    return "online" if status else "offline"


def get_api_key():
    api_key_temp = None
    api_file_path = "/app_secrets/monitoring_key"

    if os.path.exists(api_file_path) and os.path.isfile(api_file_path):
        with open(api_file_path, 'r') as api_file:
            api_file_content = api_file.read().strip()
            try:
                uuid_test = uuid.UUID(api_file_content)

                if str(uuid_test) == api_file_content:
                    api_key_temp = str(uuid_test)
            except:
                pass
    return api_key_temp


def update_router_config_timestamp():
    global remote_router_config_timestamp, api_key
    try:
        response = requests.get(f"{CONFIG_TIMESTAMP_URL}?key={api_key}")
        if response.status_code == 200:
            remote_router_config_timestamp_temp = response.json()['router_config']
            if remote_router_config_timestamp_temp != remote_router_config_timestamp:
                remote_router_config_timestamp = remote_router_config_timestamp_temp
                print(f"{datetime.now()} - Router config timestamp updated: {remote_router_config_timestamp}")
            else:
                print(f"{datetime.now()} - Router config timestamp unchanged: {remote_router_config_timestamp}")
        else:
            print(f"{datetime.now()} - Error updating router config timestamp: HTTP {response.status_code}")
    except Exception as e:
        print(f"{datetime.now()} - Exception updating router config timestamp: {e}")
    return


def fetch_host_list():
    global host_list_update_timestamp, current_router_config_timestamp, remote_router_config_timestamp, api_key
    try:
        response = requests.get(f"{HOST_LIST_URL}?key={api_key}")
        if response.status_code == 200:
            host_list_update_timestamp = time.time()
            remote_router_config_timestamp = response.json()['router_config']
            current_router_config_timestamp = remote_router_config_timestamp
            return response.json()['router_list'], True
        else:
            print(f"{datetime.now()} - Error fetching host list: HTTP {response.status_code}")
    except Exception as e:
        print(f"{datetime.now()} - Exception fetching host list: {e}")
    return [], False


def update_host_status(uuid, status):
    global notification_count, api_key
    if notification_count >= MAX_NOTIFICATIONS_PER_MONITOR_INTERVAL:
        print(f"{datetime.now()} - Notification limit reached. Skipping Remote API update for {host_list[uuid]['address']}")
        return  # Skip if notification limit is reached
    try:
        response = requests.get(f"{UPDATE_STATUS_URL}?key={api_key}&uuid={uuid}&status={get_verbose_status(status)}")
        if response.status_code == 200:
            print(f"{datetime.now()} - Remote API Status updated for {host_list[uuid]['address']} to {get_verbose_status(status)}")
            notification_count += 1
            host_list[uuid]['online'] = status
        else:
            print(f"{datetime.now()} - Error updating status for {host_list[uuid]['address']}: HTTP {response.status_code}")
    except Exception as e:
        print(f"{datetime.now()} - Exception updating status for {host_list[uuid]['address']}: {e}")


def check_host_status(host_uuid):
    command = ["fping", host_list[host_uuid]['address']]
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    current_online = True if process.returncode == 0 else False
    if DEBUG:
        print(f"{datetime.now()} - {host_list[host_uuid]['address']} is {get_verbose_status(current_online)}")
    if current_online != host_list[host_uuid]['online']:
        print(f"{datetime.now()} - Status changed for {host_list[host_uuid]['address']} to {get_verbose_status(current_online)}")
        update_host_status(host_uuid, current_online)


def update_and_monitor():
    global host_list, host_list_update_timestamp, notification_count, current_router_config_timestamp, remote_router_config_timestamp, api_key
    api_key = get_api_key()
    if not api_key:
        print(f"{datetime.now()} - Monitoring key not found or invalid. Exiting...")
        exit(1)

    while True:
        update_router_config_timestamp()
        current_time = time.time()
        notification_count = 0
        update_required = False

        if not current_router_config_timestamp:
            update_required = True
        if current_router_config_timestamp != remote_router_config_timestamp:
            update_required = True
        if current_time - host_list_update_timestamp > UPDATE_HOST_LIST_INTERVAL:
            update_required = True

        if update_required:
            print(f"{datetime.now()} - Update required. Fetching host list...")
            new_host_list, fetch_host_list_success = fetch_host_list()
            if fetch_host_list_success:
                host_list = new_host_list
                print(f"{datetime.now()} - host list updated.")
                if DEBUG:
                    print(host_list)
        else:
            print(f"{datetime.now()} - No update required. Skipping host list update.")
            if DEBUG:
                print(f"{datetime.now()} - Current router config timestamp: {current_router_config_timestamp}")
                print(f"{datetime.now()} - Remote router config timestamp: {remote_router_config_timestamp}")

        if host_list:
            if DEBUG:
                print(f"{datetime.now()} - Monitoring host... Interval between each monitor: {MONITOR_INTERVAL / len(host_list)} seconds")
            for host_uuid in host_list:
                if DEBUG:
                    print(host_list[host_uuid])
                check_host_status(host_uuid)
                time.sleep(MONITOR_INTERVAL / len(host_list))
        else:
            print(f"{datetime.now()} - No host to monitor.")
            time.sleep(MONITOR_INTERVAL)


if __name__ == "__main__":
    print(f"{datetime.now()} - Monitoring container started, waiting for routerfleet container to start...")
    if not DEBUG:
        time.sleep(30)  # Wait for the routerfleet container to start
    print(f"{datetime.now()} - Starting monitoring service...")
    update_and_monitor()


