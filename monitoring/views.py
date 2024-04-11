from django.shortcuts import render

from monitoring.models import RouterDownTime
from router_manager.models import Router
from django.http import JsonResponse
from django.utils import timezone

from routerfleet_tools.models import WebadminSettings


def view_router_config_timestamp(request):
    webadmin_settings, _ = WebadminSettings.objects.get_or_create(name='webadmin_settings')
    if not webadmin_settings.router_config_last_updated:
        webadmin_settings.router_config_last_updated = timezone.now()
    webadmin_settings.monitoring_last_run = timezone.now()
    webadmin_settings.save()
    return JsonResponse({'router_config': webadmin_settings.router_config_last_updated.isoformat()})


def view_export_router_list(request):
    router_list = {}
    webadmin_settings, _ = WebadminSettings.objects.get_or_create(name='webadmin_settings')
    webadmin_settings.monitoring_last_run = timezone.now()
    if not webadmin_settings.router_config_last_updated:
        webadmin_settings.router_config_last_updated = timezone.now()
    webadmin_settings.save()

    for router in Router.objects.filter(enabled=True, monitoring=True):
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

    webadmin_settings, _ = WebadminSettings.objects.get_or_create(name='webadmin_settings')
    webadmin_settings.monitoring_last_run = timezone.now()
    webadmin_settings.save()
    return JsonResponse({'status': 'success', 'router_config': webadmin_settings.router_config_last_updated.isoformat()})