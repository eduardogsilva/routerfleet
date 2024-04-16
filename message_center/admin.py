from django.contrib import admin
from .models import Notification, MessageChannel, Message, MessageSettings


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_type', 'router', 'router_backup', 'created', 'updated', 'uuid')
    list_filter = ('notification_type', 'router', 'router_backup', 'created', 'updated', 'uuid')
    search_fields = ('notification_type', 'router', 'router_backup', 'created', 'updated', 'uuid')
    readonly_fields = ('created', 'updated', 'uuid')


admin.site.register(Notification, NotificationAdmin)


class MessageChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled', 'channel_type', 'destination', 'token', 'status_change_offline', 'status_change_online', 'backup_fail', 'daily_status_report', 'daily_backup_report', 'created', 'updated', 'uuid')
    list_filter = ('name', 'enabled', 'channel_type', 'destination', 'token', 'status_change_offline', 'status_change_online', 'backup_fail', 'daily_status_report', 'daily_backup_report', 'created', 'updated', 'uuid')
    search_fields = ('name', 'enabled', 'channel_type', 'destination', 'token', 'status_change_offline', 'status_change_online', 'backup_fail', 'daily_status_report', 'daily_backup_report', 'created', 'updated', 'uuid')
    readonly_fields = ('created', 'updated', 'uuid')


admin.site.register(MessageChannel, MessageChannelAdmin)


class MessageAdmin(admin.ModelAdmin):
    list_display = ('channel', 'subject', 'message', 'status', 'retry_count', 'error_message', 'completed', 'created', 'updated', 'uuid')
    list_filter = ('channel', 'subject', 'message', 'status', 'retry_count', 'error_message', 'completed', 'created', 'updated', 'uuid')
    search_fields = ('channel', 'subject', 'message', 'status', 'retry_count', 'error_message', 'completed', 'created', 'updated', 'uuid')
    readonly_fields = ('created', 'updated', 'uuid')


admin.site.register(Message, MessageAdmin)


class MessageSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_length', 'max_retry', 'retry_interval', 'concatenate_status_change', 'created', 'updated', 'uuid')
    list_filter = ('name', 'max_length', 'max_retry', 'retry_interval', 'concatenate_status_change', 'created', 'updated', 'uuid')
    search_fields = ('name', 'max_length', 'max_retry', 'retry_interval', 'concatenate_status_change', 'created', 'updated', 'uuid')
    readonly_fields = ('created', 'updated', 'uuid')


admin.site.register(MessageSettings, MessageSettingsAdmin)
