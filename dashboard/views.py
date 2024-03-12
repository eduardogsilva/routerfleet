from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def view_dashboard(request):
    context = {'page_title': 'Welcome to routerfleet'}
    return render(request, 'dashboard/welcome.html', context=context)


@login_required
def view_status(request):
    context = {'page_title': 'Welcome to routerfleet'}
    return render(request, 'dashboard/status.html', context=context)
