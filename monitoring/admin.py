from django.contrib import admin
from .models import RouterDownTime


class RouterDownTimeAdmin(admin.ModelAdmin):
    list_display = ('router', 'start_time', 'end_time', 'total_down_time', 'updated', 'created', 'uuid')
    search_fields = ('router', 'start_time', 'end_time', 'total_down_time', 'updated', 'created', 'uuid')
    readonly_fields = ('updated', 'created', 'uuid')


admin.site.register(RouterDownTime, RouterDownTimeAdmin)
