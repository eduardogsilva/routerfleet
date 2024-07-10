from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CsvData, ImportTask
from .forms import CsvDataForm
from django.contrib import messages


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

