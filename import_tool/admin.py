from django.contrib import admin
from .models import CsvData, ImportTask


class CsvDataAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'created', 'updated')
    search_fields = ('uuid', 'created', 'updated')
    readonly_fields = ('uuid', 'created', 'updated')

admin.site.register(CsvData, CsvDataAdmin)


class ImportTaskAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'created', 'updated')
    search_fields = ('uuid', 'created', 'updated')
    readonly_fields = ('uuid', 'created', 'updated')

admin.site.register(ImportTask, ImportTaskAdmin)
