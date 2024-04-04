from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import ExternalIntegration
from .forms import WireGuardWebAdminForm
from django.contrib import messages
import requests
from user_manager.models import UserAcl


@login_required()
def view_wireguard_webadmin_launcher(request):
    context = {
        'page_title': 'WireGuard WebAdmin Launcher',
        'wireguard_integration': ExternalIntegration.objects.filter(name='wireguard_webadmin', integration_type='wireguard_webadmin').first()
    }
    return render(request, 'integration_manager/wireguard_webadmin_launcher.html', context=context)


@login_required()
def view_launch_wireguard_webadmin(request):
    wireguard_integration = get_object_or_404(ExternalIntegration, name='wireguard_webadmin', integration_type='wireguard_webadmin')
    api_url = f"{wireguard_integration.integration_url}/api/routerfleet_get_user_token/"
    api_url += f"?key={wireguard_integration.token}"
    api_url += f"&username={request.user.username}&action=login"
    api_url += f"&default_user_level={wireguard_integration.wireguard_webadmin_default_user_level}"
    try:
        api_response = requests.get(api_url)
    except:
        messages.warning(request, 'Error connecting to API')
        return redirect('/wireguard_webadmin/')

    try:
        if api_response.status_code == 200:
            api_json = api_response.json()
        else:
            api_json = {}
    except:
        messages.warning(request, 'Error parsing API response')
        return redirect('/wireguard_webadmin/')

    if api_response.status_code == 200:
        redirect_url = f"{wireguard_integration.integration_url}/accounts/routerfleet_authenticate_session/"
        redirect_url += f"?token={api_json.get('authentication_token')}"
        return redirect(redirect_url)
    else:
        messages.warning(request, f'Error authenticating with API. Status Code: {api_response.status_code}')
        return redirect('/wireguard_webadmin/')


@login_required()
def view_manage_wireguard_integration(request):
    if not UserAcl.objects.filter(user=request.user).filter(user_level__gte=50).exists():
        return render(request, 'access_denied.html', {'page_title': 'Access Denied'})
    context = {
        'page_title': 'Manage WireGuard WebAdmin Integration',
        'delete_confirmation_message': 'Are you sure you want to delete this integration? This action cannot be undone. Type delete in the box below to confirm.'
    }
    wireguard_integration = ExternalIntegration.objects.filter(name='wireguard_webadmin', integration_type='wireguard_webadmin').first()
    if request.GET.get('action') == 'delete':
        if request.GET.get('confirmation') == 'delete':
            wireguard_integration.delete()
            messages.success(request, 'WireGuard WebAdmin integration deleted')
            return redirect('/wireguard_webadmin/')
        else:
            messages.warning(request, 'Invalid confirmation. Integration not deleted')
            return redirect('/wireguard_webadmin/')

    form = WireGuardWebAdminForm(request.POST or None, instance=wireguard_integration, user=request.user)

    if form.is_valid():
        this_form = form.save(commit=False)
        this_form.name = 'wireguard_webadmin'
        this_form.integration_type = 'wireguard_webadmin'
        this_form.save()
        messages.success(request, 'WireGuard WebAdmin integration saved')
        return redirect('/wireguard_webadmin/')

    context['form'] = form
    return render(request, 'integration_manager/wireguard_webadmin_form.html', context=context)
