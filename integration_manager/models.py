from django.db import models


class ExternalIntegration(models.Model):
    name = models.CharField(max_length=100, unique=True)
    integration_type = models.CharField(max_length=100, choices=(('wireguard_webadmin', 'WireGuard WebAdmin'), ))
    integration_url = models.URLField()
    wireguard_webadmin_default_user_level = models.PositiveIntegerField(default=0, choices=((0, 'Do not create users'), (10, 'Debugging Analyst'), (20, 'View Only User'), (30, 'Peer Manager'), (40, 'Manager'), (50, 'Administrator')))
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
