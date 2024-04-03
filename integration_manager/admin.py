from django.contrib import admin
from .models import ExternalIntegration

class ExternalIntegrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'integration_type', 'integration_url', 'wireguard_webadmin_default_user_level', 'token', 'created_at', 'updated_at')
    search_fields = ('name', 'integration_type', 'integration_url', 'wireguard_webadmin_default_user_level', 'token', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(ExternalIntegration, ExternalIntegrationAdmin)