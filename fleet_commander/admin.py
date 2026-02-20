from django.contrib import admin

from .models import Command, CommandVariant, CommandSchedule, CommandJob, CommandTask


class CommandAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled', 'created', 'updated')
    search_fields = ('name', 'description')
    list_filter = ('enabled', 'created', 'updated')
admin.site.register(Command, CommandAdmin)

class CommandVariantAdmin(admin.ModelAdmin):
    list_display = ('command', 'router_type', 'enabled', 'created', 'updated')
    search_fields = ('command__name', 'router_type')
    list_filter = ('enabled', 'router_type', 'created', 'updated')
admin.site.register(CommandVariant, CommandVariantAdmin)

class CommandScheduleAdmin(admin.ModelAdmin):
    list_display = ('command', 'enabled', 'next_run', 'created', 'updated')
    search_fields = ('command__name',)
    list_filter = ('enabled', 'next_run', 'created', 'updated')
admin.site.register(CommandSchedule, CommandScheduleAdmin)

class CommandJobAdmin(admin.ModelAdmin):
    list_display = ('command', 'exec_source', 'user_source_name', 'task_count', 'success_count', 'error_count', 'created', 'updated')
    search_fields = ('command__name', 'user_source_name')
    list_filter = ('exec_source', 'created', 'updated')
admin.site.register(CommandJob, CommandJobAdmin)

class CommandTaskAdmin(admin.ModelAdmin):
    list_display = ('job', 'router', 'status', 'retry_count', 'created', 'updated')
    search_fields = ('job__command__name', 'router__name')
    list_filter = ('status', 'created', 'updated')
admin.site.register(CommandTask, CommandTaskAdmin)
