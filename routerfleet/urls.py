from django.contrib import admin
from django.urls import path
from dashboard.views import view_dashboard, view_status
from user_manager.views import view_manage_user, view_user_list
from accounts.views import view_login, view_logout, view_create_first_user
from router_manager.views import view_router_list, view_manage_router, view_router_group_list, view_ssh_key_list, view_manage_router_group, view_manage_sshkey, view_router_details
from backup.views import view_backup_profile_list, view_manage_backup_profile, view_backup_list, view_backup_details, view_debug_run_backups, view_compare_backups
from monitoring.views import view_export_router_list, view_update_router_status


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
    path('router/group_list/', view_router_group_list, name='router_group_list'),
    path('router/ssh_keys/', view_ssh_key_list, name='ssh_keys_list'),
    path('router/manage_group/', view_manage_router_group, name='manage_router_group'),
    path('router/manage_sshkey/', view_manage_sshkey, name='manage_sshkey'),
    path('backup/profile_list/', view_backup_profile_list, name='backup_profile_list'),
    path('backup/manage_profile/', view_manage_backup_profile, name='manage_backup_profile'),
    path('backup/backup_list/', view_backup_list, name='backup_list'),
    path('backup/backup_details/', view_backup_details, name='backup_info'),
    path('backup/compare/', view_compare_backups, name='compare_backups'),
    path('monitoring/export_router_list/', view_export_router_list, name='export_router_list'),
    path('monitoring/update_router_status/', view_update_router_status, name='update_router_status'),
]
