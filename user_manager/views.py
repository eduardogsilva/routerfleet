from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from user_manager.models import UserAcl
from .forms import UserAclForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.sessions.models import Session


@login_required
def view_user_list(request):
    if not UserAcl.objects.filter(user=request.user).filter(user_level__gte=50).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    page_title = 'User Manager'
    user_acl_list = UserAcl.objects.all().order_by('user__username')
    context = {'page_title': page_title, 'user_acl_list': user_acl_list}
    return render(request, 'user_manager/list.html', context)


@login_required
def view_manage_user(request):
    if not UserAcl.objects.filter(user=request.user).filter(user_level__gte=50).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    user_acl = None
    user = None
    if 'uuid' in request.GET:
        user_acl = get_object_or_404(UserAcl, uuid=request.GET['uuid'])
        user = user_acl.user
        form = UserAclForm(instance=user, initial={'user_level': user_acl.user_level}, user_id=user.id)
        page_title = 'Edit User ' + user.username
        if request.GET.get('action') == 'delete':
            username = user.username
            if request.GET.get('confirmation') == username:
                user.delete()
                messages.success(request, 'User deleted|The user ' + username + ' has been deleted.')
                return redirect('/user/list/')

            return redirect('/user/list/')
    else:
        form = UserAclForm()
        page_title = 'Add User'

    if request.method == 'POST':
        if user_acl:
            form = UserAclForm(request.POST, instance=user, user_id=user.id)
        else:
            form = UserAclForm(request.POST)

        if form.is_valid():
            form.save()
            if form.cleaned_data.get('password1'):
                user_disconnected = False
                if user:
                    for session in Session.objects.all():
                        if str(user.id) == session.get_decoded().get('_auth_user_id'):
                            session.delete()
                            if not user_disconnected:
                                messages.warning(request,
                                                 'User Disconnected|The user ' + user.username + ' has been disconnected.')
                                user_disconnected = True
            if user_acl:
                messages.success(request,
                                 'User updated|The user ' + form.cleaned_data['username'] + ' has been updated.')
            else:
                messages.success(request, 'User added|The user ' + form.cleaned_data['username'] + ' has been added.')
            return redirect('/user/list/')

    return render(request, 'user_manager/manage_user.html', {'form': form, 'page_title': page_title, 'user_acl': user_acl})
