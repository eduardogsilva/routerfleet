from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, get_object_or_404, redirect, Http404
from django.contrib import messages

from routerlib.backup_functions import perform_backup
from .models import BackupProfile
from .forms import BackupProfileForm
from router_manager.models import Router, BackupSchedule
from backup_data.models import RouterBackup
import difflib
import unicodedata
from routerlib.functions import gen_backup_name, get_router_backup_file_extension


@login_required()
def view_backup_profile_list(request):
    default_backup_profile, _ = BackupProfile.objects.get_or_create(name='default')
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
                if backup_profile.name == 'default':
                    messages.warning(request, 'Backup profile not deleted|Default profile cannot be deleted')
                    return redirect('backup_profile_list')
                else:
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
        form.instance.profile_error_information = ''
        form.save()
        BackupSchedule.objects.filter(router__backup_profile=form.instance).delete()
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
    hash_list = [backup.backup_text_hash]
    backup_list = []
    for backup_item in RouterBackup.objects.filter(router=backup.router, success=True).order_by('-created'):
        if backup_item.backup_text_hash and backup_item.backup_text_hash not in hash_list:
            hash_list.append(backup_item.backup_text_hash)
            backup_list.append(backup_item)
    context = {
        'backup': backup,
        'backup_list': backup_list,
        'page_title': 'Backup Details'
    }
    return render(request, 'backup/backup_details.html', context)


def normalize_text(text):
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '')
    text = '\n'.join([line.rstrip() for line in text.splitlines()])
    return text


def view_compare_backups(request):
    backup1 = get_object_or_404(RouterBackup, uuid=request.GET.get('uuid'))
    backup2 = get_object_or_404(RouterBackup, uuid=request.GET.get('compare_uuid'))
    if request.GET.get('display') == 'all':
        show_lines = 100000
        show_all = True
    else:
        show_lines = 3
        show_all = False

    diff = difflib.unified_diff(normalize_text(backup1.backup_text).splitlines(keepends=True),
                                normalize_text(backup2.backup_text).splitlines(keepends=True),
                                fromfile=backup1.backup_text_hash[:16] + '...',
                                tofile=backup2.backup_text_hash[:16] + '...',
                                lineterm='', n=show_lines)
    diff_str = '\n'.join(list(diff))

    context = {
        'backup1': backup1,
        'backup2': backup2,
        'diff_str': diff_str,
        'page_title': 'Compare Backups',
        'show_all': show_all
    }

    return render(request, 'backup/compare_backups.html', context)


def view_debug_run_backups(request):
    data = {
        'backup_count': 0,
    }
    for backup in RouterBackup.objects.filter(success=False, error=False):
        data['backup_count'] += 1
        perform_backup(backup)

    return JsonResponse(data)


@login_required()
def view_backup_download(request):
    backup = get_object_or_404(RouterBackup, uuid=request.GET.get('uuid'))
    if request.GET.get('type') == 'text':
        response = HttpResponse(backup.backup_text, content_type='text/plain')
        if backup.backup_text_filename:
            filename = backup.backup_text_filename
        else:
            filename = gen_backup_name(backup)
            filename += f'.missing_backup_name.{get_router_backup_file_extension(backup.router.router_type)["text"]}'
        print(filename)
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    elif request.GET.get('type') == 'binary':
        response = FileResponse(backup.backup_binary, as_attachment=True)
        return response
    else:
        raise Http404


@login_required()
def view_backup_delete(request):
    backup = get_object_or_404(RouterBackup, uuid=request.GET.get('uuid'))
    redirect_url = f'/router/details/?uuid={backup.router.uuid}'
    if request.GET.get('confirmation') == f'delete{backup.id}':
        backup.delete()
        messages.success(request, 'Backup deleted successfully')
        return redirect(redirect_url)
    else:
        messages.warning(request, 'Backup not deleted|Invalid confirmation')
        return redirect(f'/backup/backup_details/?uuid={backup.uuid}')
