from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Router, RouterGroup, RouterStatus, SSHKey, BackupSchedule
from .forms import RouterForm, RouterGroupForm, SSHKeyForm


@login_required
def view_router_list(request):
    router_list = Router.objects.all().order_by('name')
    filter_group = None
    if request.GET.get('filter_group'):
        if request.GET.get('filter_group') == 'all':
            pass
        else:
            filter_group = get_object_or_404(RouterGroup, uuid=request.GET.get('filter_group'))
            router_list = router_list.filter(routergroup=filter_group)

    if not filter_group and request.GET.get('filter_group') != 'all':
        filter_group = RouterGroup.objects.filter(default_group=True).first()
    context = {
        'router_list': router_list,
        'page_title': 'Router List',
        'filter_group_list': RouterGroup.objects.all().order_by('name'),
        'filter_group': filter_group,
    }
    return render(request, 'router_manager/router_list.html', context=context)


@login_required()
def view_router_details(request):
    router = get_object_or_404(Router, uuid=request.GET.get('uuid'))
    router_status, _ = RouterStatus.objects.get_or_create(router=router)
    context = {
        'router': router,
        'router_status': router_status,
        'router_backup_list': router.routerbackup_set.all().order_by('-created'),
        'page_title': 'Router Details',
    }
    return render(request, 'router_manager/router_details.html', context=context)


@login_required()
def view_manage_router(request):
    if request.GET.get('uuid'):
        router = get_object_or_404(Router, uuid=request.GET.get('uuid'))
        if request.GET.get('action') == 'delete':
            if request.GET.get('confirmation') == 'delete':
                router.delete()
                messages.success(request, 'Router deleted successfully')
                return redirect('router_list')
            else:
                messages.warning(request, 'Router not deleted|Invalid confirmation')
                return redirect('router_list')
    else:
        router = None

    form = RouterForm(request.POST or None, instance=router)
    if form.is_valid():
        form.save()
        messages.success(request, 'Router saved successfully')
        router_status, _ = RouterStatus.objects.get_or_create(router=form.instance)
        BackupSchedule.objects.filter(router=form.instance).delete()
        return redirect('router_list')

    context = {
        'form': form,
        'page_title': 'Manage Router',
        'instance': router
    }
    return render(request, 'generic_form.html', context=context)


@login_required()
def view_router_group_list(request):
    context = {
        'router_group_list': RouterGroup.objects.all().order_by('name'),
        'page_title': 'Router Group List',
    }
    return render(request, 'router_manager/router_group_list.html', context=context)


@login_required()
def view_manage_router_group(request):
    if request.GET.get('uuid'):
        router_group = get_object_or_404(RouterGroup, uuid=request.GET.get('uuid'))
        if request.GET.get('action') == 'delete':
            if request.GET.get('confirmation') == 'delete':
                router_group.delete()
                messages.success(request, 'Router Group deleted successfully')
                return redirect('router_group_list')
            else:
                messages.warning(request, 'Router Group not deleted|Invalid confirmation')
                return redirect('router_group_list')
    else:
        router_group = None

    form = RouterGroupForm(request.POST or None, instance=router_group)
    if form.is_valid():
        form.save()
        messages.success(request, 'Router Group saved successfully')
        return redirect('router_group_list')

    context = {
        'form': form,
        'page_title': 'Manage Router Group',
        'instance': router_group
    }
    return render(request, 'generic_form.html', context=context)


@login_required()
def view_ssh_key_list(request):
    context = {
        'sshkey_list': SSHKey.objects.all().order_by('name'),
        'page_title': 'SSH Key List',
    }
    return render(request, 'router_manager/sshkey_list.html', context=context)


@login_required()
def view_manage_sshkey(request):
    if request.GET.get('uuid'):
        sshkey = get_object_or_404(SSHKey, uuid=request.GET.get('uuid'))
        if request.GET.get('action') == 'delete':
            if request.GET.get('confirmation') == 'delete':
                sshkey.delete()
                messages.success(request, 'SSH Key deleted successfully')
                return redirect('ssh_keys_list')
            else:
                messages.warning(request, 'SSH Key not deleted|Invalid confirmation')
                return redirect('ssh_keys_list')
    else:
        sshkey = None

    form = SSHKeyForm(request.POST or None, instance=sshkey)
    if form.is_valid():
        form.save()
        messages.success(request, 'SSH Key saved successfully')
        return redirect('ssh_keys_list')

    context = {
        'form': form,
        'page_title': 'Manage SSH Key',
        'instance': sshkey
    }
    return render(request, 'generic_form.html', context=context)
