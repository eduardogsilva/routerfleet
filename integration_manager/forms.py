from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from .models import ExternalIntegration
import requests


class WireGuardWebAdminForm(forms.ModelForm):
    token = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = ExternalIntegration
        fields = ['integration_url', 'wireguard_webadmin_default_user_level', 'token']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(WireGuardWebAdminForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        if self.instance.pk:
            delete_html = "<a href='javascript:void(0)' class='btn btn-outline-danger' data-command='delete' onclick='openCommandDialog(this)'>Delete</a>"
            if self.instance.token:
                self.fields['token'].widget.attrs['placeholder'] = '************'
        else:
            delete_html = ''
        self.helper.layout = Layout(
            Row(
                Column('integration_url', css_class='col-md-12'),
            ),
            Row(
                Column('wireguard_webadmin_default_user_level', css_class='col-md-12'),
            ),
            Row(
                Column('token', css_class='col-md-12'),
            ),
            Row(
                Column(
                    Submit('submit', 'Salvar', css_class='btn btn-success'),
                    HTML(' <a class="btn btn-secondary" href="/wireguard_webadmin/">Back</a> '),
                    HTML(delete_html),
                    css_class='col-md-12'),
                css_class='form-row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        integration_url = cleaned_data.get('integration_url')
        wireguard_webadmin_default_user_level = cleaned_data.get('wireguard_webadmin_default_user_level')
        token = cleaned_data.get('token')
        if integration_url.endswith('/'):
            cleaned_data['integration_url'] = integration_url[:-1]
        if not token and self.instance.token:
            cleaned_data['token'] = self.instance.token

        if not integration_url.startswith('https://'):
            raise forms.ValidationError('Please use https://')

        api_test_url = f"{cleaned_data['integration_url']}/api/routerfleet_get_user_token/"
        api_test_url += f"?key={cleaned_data['token']}"
        api_test_url += f"&username={self.user.username}&action=test"

        try:
            api_test = requests.get(api_test_url)
        except:
            raise forms.ValidationError('Error connecting to API')

        try:
            if api_test.status_code == 403:
                api_response = {}
            else:
                api_response = api_test.json()
        except:
            raise forms.ValidationError('Error parsing API response')

        if api_test.status_code == 403:
            raise forms.ValidationError('Invalid token')
        elif api_test.status_code == 400:
            if api_response.get('message'):
                raise forms.ValidationError(api_response.get('message'))
            else:
                raise forms.ValidationError(f'Error authenticating with API. Status Code: {api_test.status_code}')
        elif api_test.status_code != 200:
            raise forms.ValidationError(f'Error connecting to API. Status Code: {api_test.status_code}')

        return cleaned_data


