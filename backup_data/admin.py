from django.contrib import admin
from .models import RouterBackup


class RouterBackupAdmin(admin.ModelAdmin):
    list_display = ('router', 'success', 'error', 'retry_count', 'next_retry', 'schedule_time', 'schedule_type', 'queue_length', 'finish_time', 'updated', 'created', 'uuid')
    search_fields = ('router__name', 'error_message', 'backup_text')
    list_filter = ('success', 'error', 'schedule_type')


admin.site.register(RouterBackup, RouterBackupAdmin)