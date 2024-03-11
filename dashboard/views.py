from django.shortcuts import render


def view_dashboard(request):
    context = {'page_title': 'Welcome to routerfleet'}
    return render(request, 'dashboard/welcome.html', context=context)


def view_status(request):
    context = {'page_title': 'Welcome to routerfleet'}
    return render(request, 'dashboard/status.html', context=context)
