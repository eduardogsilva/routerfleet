from django.contrib import admin
from django.urls import path
from dashboard.views import view_dashboard, view_status
from integration_manager.views import view_wireguard_webadmin_launcher, view_manage_wireguard_integration, view_launch_wireguard_webadmin
from user_manager.views import view_manage_user, view_user_list
from accounts.views import view_login, view_logout, view_create_first_user
from router_manager.views import view_router_list, view_manage_router, view_router_group_list, view_ssh_key_list, view_manage_router_group, view_manage_sshkey, view_router_details, view_create_instant_backup_task, view_router_availability
from backup.views import view_backup_profile_list, view_manage_backup_profile, view_backup_list, view_backup_details, view_debug_run_backups, view_compare_backups, view_backup_download, view_backup_delete
from monitoring.views import view_export_router_list, view_update_router_status, view_router_config_timestamp, view_router_last_status_change
from backup_data.views import view_generate_backup_schedule, view_create_backup_tasks, view_perform_backup_tasks, view_housekeeping
from routerfleet_tools.views import cron_check_updates


urlpatterns = [
    path('admin/', admin.site.urls),
    path('debug/run_backups/', view_debug_run_backups, name='debug_run_backups'),
    path('', view_dashboard, name='dashboard'),
    path('status/', view_status, name='status'),
    path('user/list/', view_user_list, name='user_list'),
    path('user/manage/', view_manage_user, name='manage_user'),
    path('accounts/create_first_user/', view_create_first_user, name='create_first_user'),
    path('accounts/login/', view_login, name='login'),
    path('accounts/logout/', view_logout, name='logout'),
    path('router/list/', view_router_list, name='router_list'),
    path('router/manage/', view_manage_router, name='manage_router'),
    path('router/details/', view_router_details, name='router_details'),
    path('router/availability/', view_router_availability, name='router_availability'),
    path('router/group_list/', view_router_group_list, name='router_group_list'),
    path('router/ssh_keys/', view_ssh_key_list, name='ssh_keys_list'),
    path('router/manage_group/', view_manage_router_group, name='manage_router_group'),
    path('router/manage_sshkey/', view_manage_sshkey, name='manage_sshkey'),
    path('router/create_instant_backup/', view_create_instant_backup_task, name='create_instant_backup_task'),
    path('backup/profile_list/', view_backup_profile_list, name='backup_profile_list'),
    path('backup/manage_profile/', view_manage_backup_profile, name='manage_backup_profile'),
    path('backup/backup_list/', view_backup_list, name='backup_list'),
    path('backup/backup_details/', view_backup_details, name='backup_info'),
    path('backup/compare/', view_compare_backups, name='compare_backups'),
    path('backup/download/', view_backup_download, name='download_backup'),
    path('backup/delete/', view_backup_delete, name='delete_backup'),
    path('monitoring/export_router_list/', view_export_router_list, name='export_router_list'),
    path('monitoring/update_router_status/', view_update_router_status, name='update_router_status'),
    path('monitoring/router_config_timestamp/', view_router_config_timestamp, name='router_config_timestamp'),
    path('monitoring/last_status_change/', view_router_last_status_change, name='last_status_change'),
    path('cron/generate_backup_schedule/', view_generate_backup_schedule, name='generate_backup_schedule'),
    path('cron/create_backup_tasks/', view_create_backup_tasks, name='create_backup_tasks'),
    path('cron/perform_backup_tasks/', view_perform_backup_tasks, name='perform_backup_tasks'),
    path('cron/housekeeping/', view_housekeeping, name='housekeeping'),
    path('cron/check_updates/', cron_check_updates, name='check_updates'),
    path('wireguard_webadmin/', view_wireguard_webadmin_launcher, name='wireguard_webadmin_launcher'),
    path('wireguard_webadmin/manage/', view_manage_wireguard_integration, name='manage_wireguard_integration'),
    path('wireguard_webadmin/launch/', view_launch_wireguard_webadmin, name='launch_wireguard_webadmin')
]
