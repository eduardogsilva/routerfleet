from django.contrib import admin
from .models import Router, SSHKey, RouterStatus, BackupSchedule


class RouterAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'username', 'router_type', 'enabled', 'monitoring')
    search_fields = ('name', 'address', 'username', 'router_type')
    list_filter = ('router_type', 'enabled', 'monitoring')


admin.site.register(Router, RouterAdmin)


class SSHKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'updated', 'created')
    search_fields = ('name',)
    list_filter = ('updated', 'created')


admin.site.register(SSHKey, SSHKeyAdmin)


class RouterStatusAdmin(admin.ModelAdmin):
    list_display = ('router', 'status_online', 'last_status_change', 'last_backup')
    search_fields = ('router', 'status_online')
    list_filter = ('status_online', 'last_status_change', 'last_backup')


admin.site.register(RouterStatus, RouterStatusAdmin)


class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = ('router', 'next_daily_backup', 'next_weekly_backup', 'next_monthly_backup')
    search_fields = ('router', 'next_daily_backup', 'next_weekly_backup', 'next_monthly_backup')
    list_filter = ('router', 'next_daily_backup', 'next_weekly_backup', 'next_monthly_backup')

admin.site.register(BackupSchedule, BackupScheduleAdmin)

