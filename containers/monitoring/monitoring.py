import requests
import time
from datetime import datetime
from subprocess import Popen, PIPE


UPDATE_HOST_LIST_INTERVAL = 600  # How often to update the router list in seconds
MONITOR_INTERVAL = 60  # How often to monitor each router in seconds
MAX_NOTIFICATIONS_PER_MONITOR_INTERVAL = 50  # Throttle the number of notifications sent to the remote API
HOST_LIST_URL = "http://127.0.0.1:8000/monitoring/export_router_list/"
UPDATE_STATUS_URL = "http://127.0.0.1:8000/monitoring/update_router_status/"
DEBUG = False

# Global variables
host_list = []
host_list_update_timestamp = 0
notification_count = 0


def get_verbose_status(status):
    return "online" if status else "offline"


def fetch_host_list():
    global host_list_update_timestamp
    try:
        print(f"{datetime.now()} - Fetching host list...")
        response = requests.get(HOST_LIST_URL)
        if response.status_code == 200:
            host_list_update_timestamp = time.time()
            return response.json()['router_list'], True
        else:
            print(f"{datetime.now()} - Error fetching host list: HTTP {response.status_code}")
    except Exception as e:
        print(f"{datetime.now()} - Exception fetching host list: {e}")
    return [], False


def update_host_status(uuid, status):
    global notification_count
    if notification_count >= MAX_NOTIFICATIONS_PER_MONITOR_INTERVAL:
        print(f"{datetime.now()} - Notification limit reached. Skipping Remote API update for {host_list[uuid]['address']}")
        return  # Skip if notification limit is reached
    try:
        response = requests.get(f"{UPDATE_STATUS_URL}?uuid={uuid}&status={get_verbose_status(status)}")
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
    global host_list, host_list_update_timestamp, notification_count
    while True:
        current_time = time.time()
        notification_count = 0

        if current_time - host_list_update_timestamp > UPDATE_HOST_LIST_INTERVAL:
            new_host_list, fetch_host_list_success = fetch_host_list()
            if fetch_host_list_success:
                host_list = new_host_list
                print(f"{datetime.now()} - host list updated.")
                if DEBUG:
                    print(host_list)

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
    update_and_monitor()


