from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import BackupProfile
from .forms import BackupProfileForm
from router_manager.models import Router
from backup_data.models import RouterBackup


@login_required()
def view_backup_profile_list(request):
    context = {
        'backup_profile_list': BackupProfile.objects.all().order_by('name'),
        'page_title': 'Backup Profiles'
    }
    return render(request, 'backup/backup_profile_list.html', context)


@login_required()
def view_manage_backup_profile(request):
    if request.GET.get('uuid'):
        backup_profile = get_object_or_404(BackupProfile, uuid=request.GET.get('uuid'))
        if request.GET.get('action') == 'delete':
            if request.GET.get('confirmation') == 'delete':
                if Router.objects.filter(backup_profile=backup_profile).exists():
                    messages.warning(request, 'Backup profile in use|Backup profile is in use and cannot be deleted')
                    return redirect('backup_profile_list')
                else:
                    backup_profile.delete()
                    messages.success(request, 'Backup profile deleted successfully')
                return redirect('backup_profile_list')
            else:
                messages.warning(request, 'Backup profile not deleted|Invalid confirmation')
                return redirect('backup_profile_list')
    else:
        backup_profile = None

    form = BackupProfileForm(request.POST or None, instance=backup_profile)
    if form.is_valid():
        form.save()
        messages.success(request, 'Backup Profile saved successfully')
        return redirect('backup_profile_list')

    context = {
        'form': form,
        'page_title': 'Manage Backup Profile',
        'instance': backup_profile
    }
    return render(request, 'backup/backup_profile_form.html', context=context)


@login_required()
def view_backup_list(request):
    backup_list = RouterBackup.objects.all().order_by('-created')
    if request.GET.get('type') == 'queue':
        backup_list = backup_list.filter(error=False, success=False).order_by('next_retry')
        view_type = 'queue'
    elif request.GET.get('type') == 'errors':
        backup_list = backup_list.filter(error=True).order_by('-created')
        view_type = 'errors'
    else:
        backup_list = backup_list.filter(success=True).order_by('-created')
        view_type = 'success'

    context = {
        'backup_list': backup_list,
        'page_title': 'Backup List',
        'view_type': view_type
    }
    return render(request, 'backup/backup_list.html', context)


@login_required()
def view_backup_details(request):
    backup = get_object_or_404(RouterBackup, uuid=request.GET.get('uuid'))
    context = {
        'backup': backup,
        'page_title': 'Backup Details'
    }
    return render(request, 'backup/backup_details.html', context)