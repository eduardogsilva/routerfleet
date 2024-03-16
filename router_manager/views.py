from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Router
from .forms import RouterForm


@login_required
def view_router_list(request):
    router_list = Router.objects.all()
    context = {
        'router_list': router_list,
        'page_title': 'Router List',

    }
    return render(request, 'router_manager/router_list.html', context=context)


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
        return redirect('router_list')

    context = {
        'form': form,
        'page_title': 'Manage Router',
        'instance': router
    }
    return render(request, 'generic_form.html', context=context)