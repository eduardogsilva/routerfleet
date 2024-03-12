from django.contrib import admin
from django.urls import path
from dashboard.views import view_dashboard, view_status
from user_manager.views import view_manage_user, view_user_list
from accounts.views import view_login, view_logout, view_create_first_user


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', view_dashboard, name='dashboard'),
    path('status/', view_status, name='status'),
    path('user/list/', view_user_list, name='user_list'),
    path('user/manage/', view_manage_user, name='manage_user'),
    path('accounts/create_first_user/', view_create_first_user, name='create_first_user'),
    path('accounts/login/', view_login, name='login'),
    path('accounts/logout/', view_logout, name='logout'),
]
