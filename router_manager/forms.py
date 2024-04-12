from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from .models import Router, RouterGroup, SSHKey
from routerlib.functions import test_authentication, connect_to_ssh
import ipaddress
import socket


class RouterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = Router
        fields = ['name', 'port', 'address', 'username', 'password', 'ssh_key', 'monitoring', 'router_type', 'enabled', 'backup_profile']

    def __init__(self, *args, **kwargs):
        super(RouterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        if self.instance.pk:
            delete_html = "<a href='javascript:void(0)' class='btn btn-outline-danger' data-command='delete' onclick='openCommandDialog(this)'>Delete</a>"
            if self.instance.password:
                self.fields['password'].widget.attrs['placeholder'] = '************'
        else:
            delete_html = ''
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('ssh_key', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('password', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('address', css_class='form-group col-md-6 mb-0'),
                Column('port', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),

            'backup_profile',
            'router_type',
            'monitoring',
            'enabled',
            Row(
                Column(
                    Submit('submit', 'Save', css_class='btn btn-success'),
                    HTML(' <a class="btn btn-secondary" href="/router/list/">Back</a> '),
                    HTML(delete_html),
                    css_class='col-md-12'),
                css_class='form-row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        ssh_key = cleaned_data.get('ssh_key')
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        address = cleaned_data.get('address')
        router_type = cleaned_data.get('router_type')
        backup_profile = cleaned_data.get('backup_profile')
        port = cleaned_data.get('port')

        if name:
            name = name.strip()
            cleaned_data['name'] = name

        if address:
            address = address.lower()
            cleaned_data['address'] = address

            try:
                socket.gethostbyname(address)
            except socket.gaierror:
                try:
                    ipaddress.ip_address(address)
                except ValueError:
                    raise forms.ValidationError('The address field must be a valid hostname or IP address.')

        if router_type == 'monitoring':
            cleaned_data['password'] = ''
            cleaned_data['ssh_key'] = None
            if backup_profile:
                raise forms.ValidationError('Monitoring only routers cannot have a backup profile')
            return cleaned_data
        else:
            if not port:
                raise forms.ValidationError('You must provide a port')
            if not 1 <= port <= 65535:
                raise forms.ValidationError('Invalid port number')

        if ssh_key and password:
            raise forms.ValidationError('You must provide a password or an SSH Key, not both')
        if not ssh_key and not password and not self.instance.password:
            raise forms.ValidationError('You must provide a password or an SSH Key')

        if not password and self.instance.password:
            cleaned_data['password'] = self.instance.password

        if ssh_key and not password:
            cleaned_data['password'] = ''


        test_authentication_success, test_authentication_message = test_authentication(
            router_type, cleaned_data['address'], port, username, cleaned_data['password'], ssh_key
        )
        if not test_authentication_success:
            if test_authentication_message:
                raise forms.ValidationError('Could not authenticate: ' + test_authentication_message)
            else:
                raise forms.ValidationError('Could not authenticate to the router. Please check the credentials and try again.')
        return cleaned_data


class RouterGroupForm(forms.ModelForm):
    class Meta:
        model = RouterGroup
        fields = ['name', 'default_group', 'internal_notes', 'routers']
        widgets = {
            'internal_notes': forms.Textarea(attrs={'rows': 4, 'cols': 40}),  # Define como um Textarea simples
        }

    def __init__(self, *args, **kwargs):
        super(RouterGroupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        if self.instance.pk:
            delete_html = "<a href='javascript:void(0)' class='btn btn-outline-danger' data-command='delete' onclick='openCommandDialog(this)'>Delete</a>"
        else:
            delete_html = ''
        self.helper.layout = Layout(
            'name',
            'internal_notes',
            'routers',
            'default_group',
            Row(
                Column(
                    Submit('submit', 'Save', css_class='btn btn-success'),
                    HTML(' <a class="btn btn-secondary" href="/router/group_list/">Back</a> '),
                    HTML(delete_html),
                    css_class='col-md-12'),
                css_class='form-row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        default_group = cleaned_data.get('default_group')

        if name:
            name = name.strip()
            cleaned_data['name'] = name

        if default_group:
            RouterGroup.objects.filter(default_group=True).update(default_group=False)
        return cleaned_data

class SSHKeyForm(forms.ModelForm):
    class Meta:
        model = SSHKey
        fields = ['name', 'public_key', 'private_key']
        widgets = {
            'public_key': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'private_key': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }

    def __init__(self, *args, **kwargs):
        super(SSHKeyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        if self.instance.pk:
            delete_html = "<a href='javascript:void(0)' class='btn btn-outline-danger' data-command='delete' onclick='openCommandDialog(this)'>Delete</a>"
        else:
            delete_html = ''
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('public_key', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column('private_key', css_class='form-group col-md-12 mb-0'),
            ),
            Row(
                Column(
                    Submit('submit', 'Save', css_class='btn btn-success'),
                    HTML(' <a class="btn btn-secondary" href="/router/ssh_keys/">Back</a> '),
                    HTML(delete_html),
                    css_class='col-md-12'),
                css_class='form-row'
            )
        )
