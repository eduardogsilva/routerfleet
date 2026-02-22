from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field, HTML
from django import forms

from router_manager.models import Router
from router_manager.models import SUPPORTED_ROUTER_TYPES
from .models import Command, CommandVariant, CommandSchedule


class CommandForm(forms.ModelForm):
    class Meta:
        model = Command
        fields = ['name', 'description', 'enabled', 'capture_output', 'max_retry', 'retry_interval']

    def __init__(self, *args, **kwargs):
        super(CommandForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        if self.instance.pk:
            back_url = f'/fleet_commander/command/details/?uuid={self.instance.uuid}'
            delete_html = (
                "<a href='javascript:void(0)' class='btn btn-outline-danger' "
                "data-command='delete' onclick='openCommandDialog(this)'>Delete</a>"
            )
        else:
            back_url = '/fleet_commander/'
            delete_html = ''

        self.helper.layout = Layout(
            Div(
                Div(Field('name'), css_class='col-md-6'),
                Div(Field('enabled'), css_class='col-md-6'),
                css_class='row',
            ),
            Div(
                Div(Field('description'), css_class='col-md-12'),
                css_class='row',
            ),
            Div(
                Div(Field('capture_output'), css_class='col-md-4'),
                Div(Field('max_retry'), css_class='col-md-4'),
                Div(Field('retry_interval'), css_class='col-md-4'),
                css_class='row',
            ),
            Div(
                Submit('submit', 'Save', css_class='btn btn-success'),
                HTML(f' <a class="btn btn-secondary" href="{back_url}">Back</a> '),
                HTML(delete_html),
                css_class='row col-md-12',
            ),
        )


class CommandExecuteForm(forms.Form):
    routers = forms.ModelMultipleChoiceField(
        queryset=Router.objects.filter(enabled=True).order_by('name'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'selectmultiple'})
    )
    router_groups = forms.ModelMultipleChoiceField(
        queryset=forms.Field().initial,  # Placeholder, will be set in __init__
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'selectmultiple'})
    )

    def __init__(self, *args, command=None, **kwargs):
        from router_manager.models import RouterGroup
        super(CommandExecuteForm, self).__init__(*args, **kwargs)
        self.command = command
        self.fields['router_groups'].queryset = RouterGroup.objects.all().order_by('name')
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        back_url = f'/fleet_commander/command/details/?uuid={command.uuid}' if command else '/fleet_commander/'
        
        self.helper.layout = Layout(
            Div(
                Div(Field('routers'), css_class='col-md-6'),
                Div(Field('router_groups'), css_class='col-md-6'),
                css_class='row',
            ),
            Div(
                Submit('submit', 'Execute Now', css_class='btn btn-primary'),
                HTML(f' <a class="btn btn-secondary" href="{back_url}">Back</a> '),
                css_class='row col-md-12',
            ),
        )


class CommandVariantForm(forms.ModelForm):
    class Meta:
        model = CommandVariant
        fields = ['router_type', 'payload', 'enabled']

    def __init__(self, *args, command=None, **kwargs):
        super(CommandVariantForm, self).__init__(*args, **kwargs)
        self.command = command
        
        existing_types = []
        if self.command:
            existing_types = list(
                CommandVariant.objects.filter(command=self.command)
                .exclude(pk=self.instance.pk if self.instance.pk else None)
                .values_list('router_type', flat=True)
            )

        valid_choices = [c for c in SUPPORTED_ROUTER_TYPES if c[0] != 'monitoring' and c[0] not in existing_types]
        self.fields['router_type'].choices = [('', '---------')] + valid_choices
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        if self.instance.pk:
            back_uuid = self.instance.command.uuid
            delete_html = (
                "<a href='javascript:void(0)' class='btn btn-outline-danger' "
                "data-command='delete' onclick='openCommandDialog(this)'>Delete</a>"
            )
        else:
            back_uuid = command.uuid if command else ''
            delete_html = ''

        self.helper.layout = Layout(
            Div(
                Div(Field('router_type'), css_class='col-md-6'),
                Div(Field('enabled'), css_class='col-md-6'),
                css_class='row',
            ),
            Div(
                Div(Field('payload'), css_class='col-md-12'),
                css_class='row',
            ),
            Div(
                Submit('submit', 'Save', css_class='btn btn-success'),
                HTML(f' <a class="btn btn-secondary" href="/fleet_commander/command/details/?uuid={back_uuid}">Back</a> '),
                HTML(delete_html),
                css_class='row col-md-12',
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        router_type = cleaned_data.get('router_type')

        if router_type and self.command:
            query = CommandVariant.objects.filter(command=self.command, router_type=router_type)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                self.add_error('router_type', 'A variant for this router type already exists for this command.')
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.command:
            instance.command = self.command
        if commit:
            instance.save()
        return instance


class CommandScheduleForm(forms.ModelForm):
    class Meta:
        model = CommandSchedule
        fields = ['enabled', 'router', 'router_group', 'start_at', 'end_at', 'repeat_interval']
        widgets = {
            'start_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, command=None, **kwargs):
        super(CommandScheduleForm, self).__init__(*args, **kwargs)
        self.command = command
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        if self.instance.pk:
            back_uuid = self.instance.command.uuid
            delete_html = (
                "<a href='javascript:void(0)' class='btn btn-outline-danger' "
                "data-command='delete' onclick='openCommandDialog(this)'>Delete</a>"
            )
        else:
            back_uuid = command.uuid if command else ''
            delete_html = ''

        self.helper.layout = Layout(
            Div(
                Div(Field('enabled'), css_class='col-md-12'),
                css_class='row',
            ),
            Div(
                Div(Field('router'), css_class='col-md-6'),
                Div(Field('router_group'), css_class='col-md-6'),
                css_class='row',
            ),
            Div(
                Div(Field('start_at'), css_class='col-md-4'),
                Div(Field('end_at'), css_class='col-md-4'),
                Div(Field('repeat_interval'), css_class='col-md-4'),
                css_class='row',
            ),
            Div(
                Submit('submit', 'Save', css_class='btn btn-success'),
                HTML(f' <a class="btn btn-secondary" href="/fleet_commander/command/details/?uuid={back_uuid}">Back</a> '),
                HTML(delete_html),
                css_class='row col-md-12',
            ),
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.command:
            instance.command = self.command
        if commit:
            instance.save()
            self.save_m2m()
        return instance
