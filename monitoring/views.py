from django.shortcuts import render, get_object_or_404

from message_center.functions import notify_router_status_update
from monitoring.models import RouterDownTime
from router_manager.models import Router, RouterStatus, RouterGroup
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from routerfleet_tools.models import WebadminSettings


def view_router_config_timestamp(request):
    if not request.user.is_authenticated and request.GET.get('key') != settings.MONITORING_KEY:
        return JsonResponse({'error': 'Not authenticated'}, status=403)
    webadmin_settings, _ = WebadminSettings.objects.get_or_create(name='webadmin_settings')
    if not webadmin_settings.router_config_last_updated:
        webadmin_settings.router_config_last_updated = timezone.now()
    webadmin_settings.monitoring_last_run = timezone.now()
    webadmin_settings.save()
    return JsonResponse({'router_config': webadmin_settings.router_config_last_updated.isoformat()})


def view_router_last_status_change(request):
    if not request.user.is_authenticated and request.GET.get('key') != settings.MONITORING_KEY:
        return JsonResponse({'error': 'Not authenticated'}, status=403)
    last_router_status_change = RouterStatus.objects.filter(last_status_change__isnull=False).order_by('-last_status_change').first()
    if last_router_status_change:
        last_status_change_timestamp = last_router_status_change.last_status_change.isoformat()
    else:
        last_status_change_timestamp = "0"
    return JsonResponse({'last_status_change': last_status_change_timestamp})


def view_export_router_list(request):
    if not request.user.is_authenticated and request.GET.get('key') != settings.MONITORING_KEY:
        return JsonResponse({'error': 'Not authenticated'}, status=403)
    webadmin_settings, _ = WebadminSettings.objects.get_or_create(name='webadmin_settings')
    # Not updating the monitoring last run here, as this view is also used on the dashboard
    if not webadmin_settings.router_config_last_updated:
        webadmin_settings.router_config_last_updated = timezone.now()
        webadmin_settings.save()

    if request.GET.get('filter_group'):
        router_group = get_object_or_404(RouterGroup, uuid=request.GET.get('filter_group'))
        query_router_list = router_group.routers.all().filter(enabled=True, monitoring=True)
    else:
        query_router_list = Router.objects.filter(enabled=True, monitoring=True)

    router_list = {}
    for router in query_router_list:
        router_list[str(router.uuid)] = {
            'address': router.address,
            'name': router.name,
            'online': router.routerstatus.status_online,
            'uuid': str(router.uuid),
        }
    data = {
        'router_list': router_list,
        'router_config': webadmin_settings.router_config_last_updated.isoformat()
    }
    return JsonResponse(data)


def view_update_router_status(request):
    if not request.user.is_authenticated and request.GET.get('key') != settings.MONITORING_KEY:
        return JsonResponse({'error': 'Not authenticated'}, status=403)
    router = Router.objects.get(uuid=request.GET.get('uuid'))
    new_status = request.GET.get('status')
    if router.routerstatus.status_online:
        current_status = 'online'
    else:
        current_status = 'offline'
    if new_status not in ['online', 'offline']:
        return JsonResponse({'status': 'error', 'error_message': 'Invalid status'}, status=400)
    if new_status == 'online':
        router.routerstatus.status_online = True
    else:
        router.routerstatus.status_online = False
    router.routerstatus.save()

    if current_status != new_status:
        if new_status == 'online':
            router.routerstatus.status_online = True
            downtime = RouterDownTime.objects.filter(router=router, end_time=None).first()
            if downtime:
                downtime.end_time = timezone.now()
                downtime.save()
        else:
            router.routerstatus.status_online = False
            downtime = RouterDownTime.objects.create(router=router, start_time=timezone.now())
        router.routerstatus.last_status_change = timezone.now()
        router.routerstatus.save()
        if downtime:
            RouterDownTime.objects.filter(router=router, end_time=None).exclude(uuid=downtime.uuid).delete()
        notify_router_status_update(router)

    webadmin_settings, _ = WebadminSettings.objects.get_or_create(name='webadmin_settings')
    webadmin_settings.monitoring_last_run = timezone.now()
    webadmin_settings.save()
    return JsonResponse({'status': 'success', 'router_config': webadmin_settings.router_config_last_updated.isoformat()})