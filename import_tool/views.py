from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import CsvData, ImportTask
from .forms import CsvDataForm


@login_required()
def view_import_tool_list(request):
    import_list = CsvData.objects.all().order_by('-created')
    data = {
        'import_list': import_list,
        'page_title': 'CSV import List',
    }
    return render(request, 'import_tool/import_tool_list.html', context=data)


@login_required()
def view_import_csv_file(request):
    form = CsvDataForm(request.POST or None)
    data = {'form': form, 'page_title': 'Import CSV File'}

    return render(request, 'generic_form.html', context=data)
