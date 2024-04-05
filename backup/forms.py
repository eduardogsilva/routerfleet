from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Field, Div
from .models import BackupProfile


class BackupProfileForm(forms.ModelForm):
    class Meta:
        model = BackupProfile
        fields = [
            'name', 'daily_backup', 'weekly_backup', 'monthly_backup',
            'daily_retention', 'weekly_retention', 'monthly_retention',
            'retain_backups_on_error', 'daily_day_monday', 'daily_day_tuesday',
            'daily_day_wednesday', 'daily_day_thursday', 'daily_day_friday',
            'daily_day_saturday', 'daily_day_sunday', 'weekly_day',
            'monthly_day', 'daily_hour', 'weekly_hour', 'monthly_hour',
            'max_retry', 'retry_interval', 'backup_interval', 'retrieve_interval', 'instant_retention'
        ]
        # widgets = {
        #     'weekly_day': forms.Select(),
        #     'monthly_day': forms.Select(),
        #     'daily_hour': forms.Select(choices=HOUR_CHOICES),
        #     'weekly_hour': forms.Select(choices=HOUR_CHOICES),
        #     'monthly_hour': forms.Select(choices=HOUR_CHOICES),
        #     'max_retry': forms.Select(),
        #     'retry_interval': forms.Select(),
        #     'backup_interval': forms.Select(),
        # }

    def __init__(self, *args, **kwargs):
        super(BackupProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        if self.instance.pk and self.instance.name != 'default':
            delete_html = "<a href='javascript:void(0)' class='btn btn-outline-danger' data-command='delete' onclick='openCommandDialog(this)'>Delete</a>"
        else:
            delete_html = ''

        self.fields['daily_day_monday'].label = 'Monday'
        self.fields['daily_day_tuesday'].label = 'Tuesday'
        self.fields['daily_day_wednesday'].label = 'Wednesday'
        self.fields['daily_day_thursday'].label = 'Thursday'
        self.fields['daily_day_friday'].label = 'Friday'
        self.fields['daily_day_saturday'].label = 'Saturday'
        self.fields['daily_day_sunday'].label = 'Sunday'
        self.fields['daily_backup'].label = 'Daily'
        self.fields['weekly_backup'].label = 'Weekly'
        self.fields['monthly_backup'].label = 'Monthly'
        self.fields['daily_retention'].label = 'Retention (days)'
        self.fields['weekly_retention'].label = 'Retention (days)'
        self.fields['monthly_retention'].label = 'Retention (days)'
        self.fields['instant_retention'].label = 'Instant Retention (days)'
        if self.instance.pk and self.instance.name == 'default':
            self.fields['name'].widget.attrs['readonly'] = True

        self.helper.layout = Layout(
            Div(Div('name', css_class='col-md-12'), css_class='row'),
            Div(
                Div('daily_backup', css_class='col-md-4'),
                Div('weekly_backup', css_class='col-md-4'),
                Div('monthly_backup', css_class='col-md-4'),
            css_class='row'),

            Div(
                Div(HTML('<hr><h4>Daily Backups</h4>'), css_class='col-md-12'),
                Div('daily_hour', css_class='col-md-6'),
                Div('daily_retention', css_class='col-md-6'),
                Div('daily_day_monday', css_class='col-md-4'),
                Div('daily_day_tuesday', css_class='col-md-4'),
                Div('daily_day_wednesday', css_class='col-md-4'),
                Div('daily_day_thursday',css_class='col-md-4'),
                Div('daily_day_friday', css_class='col-md-4'),
                Div('daily_day_saturday', css_class='col-md-4'),
                Div('daily_day_sunday', css_class='col-md-4'),
                css_id='daily_settings', css_class='row'
            ),

            Div(
                Div(HTML('<hr><h4>Weekly Backups</h4>'), css_class='col-md-12'),
                Div('weekly_hour', css_class='col-md-6'),
                Div('weekly_day', css_class='col-md-6'),
                Div('weekly_retention', css_class='col-md-6'),

                css_id='weekly_settings', css_class='row'
            ),

            Div(
                Div(HTML('<hr><h4>Monthly Backups</h4>'), css_class='col-md-12'),
                Div('monthly_hour', css_class='col-md-6'),
                Div('monthly_day', css_class='col-md-6'),
                Div('monthly_retention', css_class='col-md-6'),

                css_id='monthly_settings', css_class='row'
            ),

            Div(
                Div(HTML('<hr><h4>Backup Settings</h4>'), css_class='col-md-12'),
                Div('max_retry', css_class='col-md-6'),
                Div('retry_interval', css_class='col-md-6'),
                Div('backup_interval', css_class='col-md-6'),
                Div('retrieve_interval', css_class='col-md-6'),
                Div('instant_retention', css_class='col-md-6'),
                Div('retain_backups_on_error', css_class='col-md-12'),
                css_id='misc_settings', css_class='row'
            ),
            Row(
                Column(
                    Submit('submit', 'Save', css_class='btn btn-success'),
                    HTML(' <a class="btn btn-secondary" href="/backup/profile_list/">Back</a> '),
                    HTML(delete_html),
                    css_class='col-md-12'
                )
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        daily_backup = cleaned_data.get('daily_backup')
        weekly_backup = cleaned_data.get('weekly_backup')
        monthly_backup = cleaned_data.get('monthly_backup')

        daily_day_monday = cleaned_data.get('daily_day_monday')
        daily_day_tuesday = cleaned_data.get('daily_day_tuesday')
        daily_day_wednesday = cleaned_data.get('daily_day_wednesday')
        daily_day_thursday = cleaned_data.get('daily_day_thursday')
        daily_day_friday = cleaned_data.get('daily_day_friday')
        daily_day_saturday = cleaned_data.get('daily_day_saturday')
        daily_day_sunday = cleaned_data.get('daily_day_sunday')
        name = cleaned_data.get('name')

        if self.instance.pk:
            if self.instance.name == 'default' and name != 'default':
                raise forms.ValidationError('You cannot change the default profile name')

        if daily_backup:
            if not daily_day_monday and not daily_day_tuesday and not daily_day_wednesday and not daily_day_thursday and not daily_day_friday and not daily_day_saturday and not daily_day_sunday:
                raise forms.ValidationError('You must select at least one day for daily backups')

        if not daily_backup and not weekly_backup and not monthly_backup:
            raise forms.ValidationError('You must select at least one backup type')

        return cleaned_data
