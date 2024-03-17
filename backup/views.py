from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import BackupProfile
from .forms import BackupProfileForm
from router_manager.models import Router


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
