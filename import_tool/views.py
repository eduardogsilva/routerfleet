from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from backup.models import BackupProfile
from router_manager.models import Router, SSHKey, SUPPORTED_ROUTER_TYPES, RouterGroup
from routerlib.functions import test_authentication
from .models import CsvData, ImportTask
from .forms import CsvDataForm
from django.contrib import messages
import ipaddress
import socket

SUPPORTED_ROUTER_TYPES = [rt[0] for rt in SUPPORTED_ROUTER_TYPES]


@login_required()
def run_import_task(request):
    import_task = get_object_or_404(ImportTask, uuid=request.GET.get('uuid'), import_success=False, import_error=False)
    ssh_key = None
    backup_profile = None
    router_group = None

    name = import_task.name.strip()

    if Router.objects.filter(name=name).exists():
        error_message = f'Router with name "{name}" already exists.'
        import_task.import_error = True
        import_task.import_error_message = error_message
        import_task.save()
        return JsonResponse({'status': 'error', 'error_message': error_message})

    if import_task.ssh_key_name:
        ssh_key = SSHKey.objects.filter(name=import_task.ssh_key_name).first()
        if not ssh_key:
            error_message = f'SSH Key with name "{import_task.ssh_key_name}" not found.'
            import_task.import_error = True
            import_task.import_error_message = error_message
            import_task.save()
            return JsonResponse({'status': 'error', 'error_message': error_message})

    address = import_task.address.lower()
    try:
        socket.gethostbyname(address)
    except socket.gaierror:
        try:
            ipaddress.ip_address(address)
        except ValueError:
            error_message = 'The address field must be a valid hostname or IP address.'
            import_task.import_error = True
            import_task.import_error_message = error_message
            import_task.save()
            return JsonResponse({'status': 'error', 'error_message': error_message})

    if not 1 <= import_task.port <= 65535:
        error_message = 'Invalid port number'
        import_task.import_error = True
        import_task.import_error_message = error_message
        import_task.save()
        return JsonResponse({'status': 'error', 'error_message': error_message})

    if import_task.router_type not in SUPPORTED_ROUTER_TYPES:
        error_message = f'Invalid router_type "{import_task.router_type}"'
        import_task.import_error = True
        import_task.import_error_message = error_message
        import_task.save()
        return JsonResponse({'status': 'error', 'error_message': error_message})

    if import_task.backup_profile_name:
        backup_profile = BackupProfile.objects.filter(name=import_task.backup_profile_name).first()
        if not backup_profile:
            error_message = f'Backup Profile with name "{import_task.backup_profile_name}" not found.'
            import_task.import_error = True
            import_task.import_error_message = error_message
            import_task.save()
            return JsonResponse({'status': 'error', 'error_message': error_message})

    if import_task.router_group_name:
        router_group = RouterGroup.objects.filter(name=import_task.router_group_name).first()
        if not router_group:
            error_message = f'Router Group with name "{import_task.router_group_name}" not found.'
            import_task.import_error = True
            import_task.import_error_message = error_message
            import_task.save()
            return JsonResponse({'status': 'error', 'error_message': error_message})

    if not import_task.password and not ssh_key:
        error_message = 'You must provide a password or an SSH Key'
        import_task.import_error = True
        import_task.import_error_message = error_message
        import_task.save()
        return JsonResponse({'status': 'error', 'error_message': error_message})

    test_authentication_success, test_authentication_message = test_authentication(
        import_task.router_type, address, import_task.port, import_task.username, import_task.password, ssh_key
    )
    if not test_authentication_success:
        if test_authentication_message:
            error_message = 'Could not authenticate: ' + test_authentication_message
        else:
            error_message = 'Could not authenticate to the router. Please check the credentials and try again.'
        import_task.import_error = True
        import_task.import_error_message = error_message
        import_task.save()
        return JsonResponse({'status': 'error', 'error_message': error_message})


    new_router = Router.objects.create(
        name=import_task.name, username=import_task.username, password=import_task.password, ssh_key=ssh_key,
        address=address, port=import_task.port, router_type=import_task.router_type, backup_profile=backup_profile,
        monitoring=import_task.monitoring
    )

    if router_group:
        router_group.routers.add(new_router)
        router_group.save()

    import_task.router = new_router
    import_task.import_success = True
    import_task.ssh_key = ssh_key
    import_task.backup_profile = backup_profile
    import_task.router_group = router_group
    import_task.save()

    return JsonResponse({'status': 'success', 'message': 'Task completed successfully.'})


@login_required()
def view_import_tool_list(request):
    import_list = []
    for csv_data in CsvData.objects.all().order_by('-created'):
        import_summary = {
            'csv_data': csv_data,
            'task_count': csv_data.importtask_set.filter(csv_data=csv_data).count(),
            'success_count': csv_data.importtask_set.filter(csv_data=csv_data, import_success=True).count(),
            'error_count': csv_data.importtask_set.filter(csv_data=csv_data, import_error=True).count(),
        }
        if import_summary['task_count'] != import_summary['success_count'] + import_summary['error_count']:
            import_summary['status'] = 'In Progress'
        elif import_summary['error_count'] > 0:
            import_summary['status'] = 'Completed with Errors'
        else:
            import_summary['status'] = 'Completed'
        import_list.append(import_summary)
    data = {
        'import_list': import_list,
        'page_title': 'CSV import List',
    }
    return render(request, 'import_tool/import_tool_list.html', context=data)


@login_required()
def view_import_details(request):
    csv_data = get_object_or_404(CsvData, uuid=request.GET.get('uuid'))
    import_task_list = ImportTask.objects.filter(csv_data=csv_data).order_by('import_id')
    if request.GET.get('view') == 'raw':
        import_view = 'raw'
    elif request.GET.get('view') == 'processed':
        import_view = 'processed'
    else:
        import_view = 'tasks'

    if request.GET.get('action') == 'create_tasks':
        tasks_created = 0
        for task in csv_data.import_data:
            import_task, import_task_created = ImportTask.objects.get_or_create(
                csv_data=csv_data, import_id=task['import_id'], defaults={
                    'name': task['name'],
                    'username': task['username'],
                    'password': task['password'],
                    'address': task['address'],
                    'port': task['port'],
                    'router_type': task['router_type'],
                    'backup_profile_name': task['backup_profile'],
                    'router_group_name': task['router_group'],
                    'ssh_key_name': task['ssh_key'],
                    'monitoring': True if task['monitoring'] == 'true' else False,
                }
            )
            if import_task_created:
                tasks_created += 1
        if tasks_created > 0:
            messages.success(request, f'Tasks created: {tasks_created}')
        else:
            messages.warning(request, 'No new tasks created.')
        return redirect(f'/router/import_tool/details/?uuid={csv_data.uuid}')

    elif request.GET.get('action') == 'start_import':
        import_view = 'tasks'
        pass

    elif request.GET.get('action') == 'delete_errors':
        tasks_deleted = 0
        for task in import_task_list.filter(import_error=True):
            task.delete()
            tasks_deleted += 1
        if tasks_deleted > 0:
            messages.success(request, f'Error tasks deleted: {tasks_deleted}')
        else:
            messages.warning(request, 'No error tasks deleted.')
        return redirect(f'/router/import_tool/details/?uuid={csv_data.uuid}')

    elif request.GET.get('action') == 'delete':
        #import_task_list.delete()
        #csv_data.delete()
        messages.warning(request, 'Delete action not implemented yet.')
        return redirect('/router/import_tool')

    data = {
        'csv_data': csv_data,
        'import_task_list': import_task_list,
        'import_view': import_view,
        'page_title': f'Import Details - {csv_data.id}',
    }
    return render(request, 'import_tool/import_details.html', context=data)


@login_required()
def view_import_csv_file(request):
    form = CsvDataForm(request.POST or None)
    data = {'form': form, 'page_title': 'Import CSV File'}
    if form.is_valid():
        csv_data_instance = form.save(commit=False)
        csv_data_instance.import_data = form.cleaned_data['import_data']
        csv_data_instance.save()

        messages.success(request, 'CSV data successfully processed and saved.')
        return redirect('success_url')

    return render(request, 'generic_form.html', context=data)

