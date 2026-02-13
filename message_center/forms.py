import requests
from .models import MessageSettings, MessageChannel

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, Field, HTML
from crispy_forms.bootstrap import FormActions, StrictButton
from django.core.exceptions import ValidationError
from datetime import datetime


class MessageSettingsForm(forms.ModelForm):
    class Meta:
        model = MessageSettings
        fields = [
            'max_length', 'max_retry', 'retry_interval', 'concatenate_status_change', 'status_change_delay',
            'concatenate_backup_fails', 'backup_fails_delay', 'daily_report_time'
        ]

    def __init__(self, *args, **kwargs):
        super(MessageSettingsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Message Settings',
            ),
            Div(
                Div(Field('max_length'), css_class='col-md-6'),
                Div(Field('daily_report_time'), css_class='col-md-6'),
                css_class='row'),
            Div(
                Div(Field('max_retry'), css_class='col-md-6'),
                Div(Field('retry_interval'), css_class='col-md-6'),
                css_class='row'),
            Div(
                Div(
                    Div(
                        Div(Field('concatenate_status_change'), css_class='col-md-12'),
                        Div(Field('status_change_delay'), css_class='col-md-12'),
                        css_class='row'),
                    css_class='col-md-6'),
                Div(
                    Div(
                        Div(Field('concatenate_backup_fails'), css_class='col-md-12'),
                        Div(Field('backup_fails_delay'), css_class='col-md-12'),
                        css_class='row'),
                    css_class='col-md-6'),
                css_class='row'),
            Div(
                Div(
                    Submit('submit', 'Save', css_class='btn btn-success'),
                    HTML(' <a class="btn btn-secondary" href="/message_center/channel_list/">Back</a> '),
                    css_class='col-md-12'
                ),
            css_class='row')
        )

    def clean(self):
        cleaned_data = super().clean()

        max_length = cleaned_data.get('max_length')
        if max_length is not None and (max_length < 500 or max_length > 2000):
            self.add_error('max_length', 'Max length must be between 500 and 2000.')

        daily_report_time = cleaned_data.get('daily_report_time')
        if daily_report_time is not None:
            try:
                datetime.strptime(daily_report_time, '%H:%M')
            except ValueError:
                self.add_error('daily_report_time', 'Invalid time format. Use HH:MM.')

        max_retry = cleaned_data.get('max_retry')
        if max_retry is not None and (max_retry < 0 or max_retry > 5):
            self.add_error('max_retry', 'Max retry must be between 0 and 5.')

        retry_interval = cleaned_data.get('retry_interval')
        if retry_interval is not None and (retry_interval < 30 or retry_interval > 600):
            self.add_error('retry_interval', 'Retry interval must be between 30 and 600 seconds.')

        status_change_delay = cleaned_data.get('status_change_delay')
        if status_change_delay is not None and (status_change_delay < 60 or status_change_delay > 600):
            self.add_error('status_change_delay', 'Status change delay must be between 60 and 600 seconds.')

        backup_fails_delay = cleaned_data.get('backup_fails_delay')
        if backup_fails_delay is not None and (backup_fails_delay < 60 or backup_fails_delay > 3600):
            self.add_error('backup_fails_delay', 'Backup fails delay must be between 60 and 3600 seconds.')
        return cleaned_data


class MessageChannelForm(forms.ModelForm):
    class Meta:
        model = MessageChannel
        fields = [
            'name', 'enabled', 'channel_type', 'destination', 'token', 'status_change_offline', 'status_change_online',
            'backup_fail', 'daily_status_report', 'daily_backup_report'
        ]

    def __init__(self, *args, **kwargs):
        super(MessageChannelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields['enabled'].label = 'Channel Enabled'
        self.helper.layout = Layout(
            Fieldset(
                'Message Channel',
            ),
            Div(
                Div(Field('name'), css_class='col-md-6'),
                Div(Field('channel_type'), css_class='col-md-6'),
                css_class='row'),
            Div(
                Div(Field('destination'), css_class='col-md-6'),
                Div(Field('token'), css_class='col-md-6'),
                css_class='row'),

            Div(
                Div(
                    Div(HTML('<h4>Notification Settings</h4>'), css_class='col-md-12'),

                    Div(Field('status_change_offline'), css_class='col-md-6'),
                    Div(Field('status_change_online'), css_class='col-md-6'),
                    Div(Field('daily_status_report'), css_class='col-md-6'),
                    Div(Field('daily_backup_report'), css_class='col-md-6'),
                    Div(Field('backup_fail'), css_class='col-md-6'),
                    Div(Field('enabled'), css_class='col-md-6'),
                    css_class='row'),
                Div(
                    Submit('submit', 'Save', css_class='btn btn-success'),
                    HTML(' <a class="btn btn-secondary" href="/message_center/channel_list/">Back</a> '),
                    css_class='col-md-12'
                ),
            css_class='row')
        )

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        enabled = cleaned_data.get('enabled')

        destination = cleaned_data.get('destination')
        if destination is not None and len(destination) > 100:
            self.add_error('destination', 'Destination must be less than 100 characters.')

        token = cleaned_data.get('token')
        if token is not None and len(token) > 100:
            self.add_error('token', 'Token must be less than 100 characters.')

        channel_type = cleaned_data.get('channel_type')
        if channel_type == 'ntfy':
            if not destination:
                 self.add_error('destination', 'ntfy.sh requires a destination (topic name).')
            
            if token:
                 self.cleaned_data['token'] = ''

        test_message = 'Test message from RouterFleet'
        remote_error = 'No error message received'

        if channel_type == 'callmebot' and enabled:
            if not token or not destination:
                raise forms.ValidationError('CallMeBot requires a token and destination.')

            message = requests.get(f'https://api.callmebot.com/whatsapp.php?phone={destination}&text={test_message}&apikey={token}')
            if message.status_code != 200:
                if message.text:
                    remote_error = message.text[:200]
                raise forms.ValidationError(f'Test message failed. CallMeBot API status code {message.status_code}. Error: {remote_error}')

        elif channel_type == 'telegram' and enabled:
            if not token or not destination:
                raise forms.ValidationError('Telegram requires a token and destination.')
            message = requests.get(f'https://api.telegram.org/bot{token}/sendMessage?chat_id={destination}&text={test_message}')
            if message.status_code != 200:
                if message.text:
                    remote_error = message.text[:200]
                raise forms.ValidationError(f'Test message failed. Telegram API status code {message.status_code}. Error: {remote_error}')

        elif channel_type == 'ntfy' and enabled:
            if not destination:
                raise forms.ValidationError('ntfy.sh requires a destination.')

            try:
                message = requests.post(f'https://ntfy.sh/{destination}', data=test_message.encode('utf-8'))
                if message.status_code != 200:
                   if message.text:
                       remote_error = message.text[:200]
                   raise forms.ValidationError(f'Test message failed. ntfy.sh API status code {message.status_code}. Error: {remote_error}')
            except requests.exceptions.RequestException as e:
                raise forms.ValidationError(f'Test message failed. Network error: {str(e)}')

        return cleaned_data
