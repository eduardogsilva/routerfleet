from django.contrib import admin
from django.urls import path
from dashboard.views import view_dashboard, view_status


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', view_dashboard, name='dashboard'),
    path('status/', view_status, name='status')
]
