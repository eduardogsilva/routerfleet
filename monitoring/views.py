from django.shortcuts import render
from router_manager.models import Router
from django.http import JsonResponse


def view_export_router_list(request):
    router_list = {}
    for router in Router.objects.filter(enabled=True, monitoring=True):
        router_list[str(router.uuid)] = {
            'address': router.address,
            'name': router.name,
            'online': router.routerstatus.status_online,
            'uuid': str(router.uuid),
        }
    data = {
        'router_list': router_list
    }
    return JsonResponse(data)


def view_update_router_status(request):
    router = Router.objects.get(uuid=request.GET.get('uuid'))
    new_status = request.GET.get('status')
    if new_status not in ['online', 'offline']:
        return JsonResponse({'status': 'error', 'error_message': 'Invalid status'}, status=400)
    if new_status == 'online':
        router.routerstatus.status_online = True
    else:
        router.routerstatus.status_online = False
    router.routerstatus.save()
    return JsonResponse({'status': 'success'})