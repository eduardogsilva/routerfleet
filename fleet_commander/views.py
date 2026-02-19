from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from user_manager.models import UserAcl
from .forms import CommandForm, CommandVariantForm, CommandScheduleForm
from .models import Command, CommandVariant, CommandSchedule, CommandJob, CommandTask


@login_required()
def view_command_list(request):
    if not UserAcl.objects.filter(user=request.user, user_level__gte=20).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    context = {
        'command_list': Command.objects.all().order_by('name'),
        'page_title': 'Fleet Commander',
    }
    return render(request, 'fleet_commander/command_list.html', context)


@login_required()
def view_command_details(request):
    if not UserAcl.objects.filter(user=request.user, user_level__gte=20).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    command = get_object_or_404(Command, uuid=request.GET.get('uuid'))
    context = {
        'command': command,
        'variant_list': command.variants.all().order_by('router_type'),
        'schedule_list': command.schedules.all().order_by('-created'),
        'page_title': command.name,
    }
    return render(request, 'fleet_commander/command_details.html', context)


@login_required()
def view_manage_command(request):
    if not UserAcl.objects.filter(user=request.user, user_level__gte=40).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})

    if request.GET.get('uuid'):
        command = get_object_or_404(Command, uuid=request.GET.get('uuid'))
        if request.GET.get('action') == 'delete':
            if request.GET.get('confirmation') == 'delete':
                command.delete()
                messages.success(request, 'Command deleted successfully')
            else:
                messages.warning(request, 'Command not deleted|Invalid confirmation')
            return redirect('/fleet_commander/')
    else:
        command = None

    form = CommandForm(request.POST or None, instance=command)
    if form.is_valid():
        form.save()
        messages.success(request, 'Command saved successfully')
        return redirect('/fleet_commander/')

    context = {
        'form': form,
        'page_title': 'Manage Command',
        'instance': command,
    }
    return render(request, 'generic_form.html', context)


@login_required()
def view_manage_command_variant(request):
    if not UserAcl.objects.filter(user=request.user, user_level__gte=40).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})

    command = get_object_or_404(Command, uuid=request.GET.get('command_uuid'))

    if request.GET.get('uuid'):
        variant = get_object_or_404(CommandVariant, uuid=request.GET.get('uuid'))
        if request.GET.get('action') == 'delete':
            if request.GET.get('confirmation') == 'delete':
                variant.delete()
                messages.success(request, 'Variant deleted successfully')
            else:
                messages.warning(request, 'Variant not deleted|Invalid confirmation')
            return redirect(f'/fleet_commander/command/details/?uuid={command.uuid}')
    else:
        variant = None

    form = CommandVariantForm(request.POST or None, instance=variant, command=command)
    if form.is_valid():
        form.save()
        messages.success(request, 'Variant saved successfully')
        return redirect(f'/fleet_commander/command/details/?uuid={command.uuid}')

    context = {
        'form': form,
        'page_title': 'Manage Variant',
        'instance': variant,
    }
    return render(request, 'generic_form.html', context)


@login_required()
def view_manage_command_schedule(request):
    if not UserAcl.objects.filter(user=request.user, user_level__gte=40).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})

    command = get_object_or_404(Command, uuid=request.GET.get('command_uuid'))

    if request.GET.get('uuid'):
        schedule = get_object_or_404(CommandSchedule, uuid=request.GET.get('uuid'))
        if request.GET.get('action') == 'delete':
            if request.GET.get('confirmation') == 'delete':
                schedule.delete()
                messages.success(request, 'Schedule deleted successfully')
            else:
                messages.warning(request, 'Schedule not deleted|Invalid confirmation')
            return redirect(f'/fleet_commander/command/details/?uuid={command.uuid}')
    else:
        schedule = None

    form = CommandScheduleForm(request.POST or None, instance=schedule, command=command)
    if form.is_valid():
        saved = form.save()
        saved.update_next_run()
        messages.success(request, 'Schedule saved successfully')
        return redirect(f'/fleet_commander/command/details/?uuid={command.uuid}')

    context = {
        'form': form,
        'page_title': 'Manage Schedule',
        'instance': schedule,
    }
    return render(request, 'generic_form.html', context)


@login_required()
def view_job_list(request):
    if not UserAcl.objects.filter(user=request.user, user_level__gte=20).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    context = {
        'job_list': CommandJob.objects.all().select_related('command').order_by('-created'),
        'page_title': 'Job History',
    }
    return render(request, 'fleet_commander/job_list.html', context)


@login_required()
def view_job_details(request):
    if not UserAcl.objects.filter(user=request.user, user_level__gte=20).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    job = get_object_or_404(CommandJob, uuid=request.GET.get('uuid'))
    context = {
        'job': job,
        'task_list': job.tasks.all().order_by('-created'),
        'page_title': f'Job: {job.command.name}',
    }
    return render(request, 'fleet_commander/job_details.html', context)


@login_required()
def view_task_details(request):
    if not UserAcl.objects.filter(user=request.user, user_level__gte=20).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    task = get_object_or_404(CommandTask, uuid=request.GET.get('uuid'))
    context = {
        'task': task,
        'page_title': f'Task: {task.router_name or task.router_uuid}',
    }
    return render(request, 'fleet_commander/task_details.html', context)
