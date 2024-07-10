from router_manager.models import SUPPORTED_ROUTER_TYPES

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from .models import CsvData
import csv
import io
import re
from django.core.exceptions import ValidationError

SUPPORTED_ROUTER_TYPES = [rt[0] for rt in SUPPORTED_ROUTER_TYPES]


class CsvDataForm(forms.ModelForm):
    class Meta:
        model = CsvData
        fields = ['raw_csv_data']

    def __init__(self, *args, **kwargs):
        super(CsvDataForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('raw_csv_data', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column(
                    Submit('submit', 'Save', css_class='btn btn-success'),
                    HTML(' <a class="btn btn-secondary" href="/router/import_tool/">Back</a> '),
                    css_class='col-md-12'),
                css_class='form-row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        raw_csv_data = cleaned_data.get('raw_csv_data')

        expected_fields = [
            'name', 'username', 'password', 'ssh_key', 'address', 'port', 'router_type',
            'backup_profile', 'router_group', 'monitoring'
        ]

        if raw_csv_data:
            csv_file = io.StringIO(raw_csv_data)
            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                raise ValidationError("The input is not a valid CSV file or it's empty.")

            if reader.fieldnames != expected_fields:
                raise ValidationError(f"The CSV header does not match the expected format. Expected fields: {expected_fields}")

            required_fields = {'name', 'username', 'address', 'port', 'router_type', 'monitoring'}
            optional_fields = {'backup_profile', 'router_group'}
            valid_fields = required_fields | optional_fields | {'password', 'ssh_key'}
            seen_names = set()

            for line_number, row in enumerate(reader, start=2):  # start=2 to account for the header
                if not any(row.values()):
                    continue  # Skip empty lines

                missing_fields = required_fields - row.keys()
                if missing_fields:
                    raise ValidationError(f"Missing required fields: {missing_fields} on line {line_number}")

                extra_fields = set(row.keys()) - valid_fields
                if extra_fields:
                    raise ValidationError(f"Unexpected fields: {extra_fields} on line {line_number}")

                if not (row.get('password') or row.get('ssh_key')):
                    raise ValidationError(f"Either 'password' or 'ssh_key' must be provided on line {line_number}")
                if row.get('password') and row.get('ssh_key'):
                    raise ValidationError(f"Both 'password' and 'ssh_key' cannot be provided together on line {line_number}")

                if row['name'] in seen_names:
                    raise ValidationError(f"Duplicate name '{row['name']}' found on line {line_number}")
                seen_names.add(row['name'])

                if row['router_type'] not in SUPPORTED_ROUTER_TYPES:
                    raise ValidationError(f"Invalid router_type '{row['router_type']}' on line {line_number}")

                if row['monitoring'].lower() not in {'true', 'false'}:
                    raise ValidationError(f"Invalid value for 'monitoring' on line {line_number}. Must be 'true' or 'false'.")

                if not self._is_valid_ip_or_hostname(row['address']):
                    raise ValidationError(f"Invalid address '{row['address']}' on line {line_number}")

                if not row['port'].isdigit() or not (1 <= int(row['port']) <= 65535):
                    raise ValidationError(f"Invalid port '{row['port']}' on line {line_number}")

        return cleaned_data

    def _is_valid_ip_or_hostname(self, value):
        ip_pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
        hostname_pattern = re.compile(r"^(?=.{1,253}$)(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,6}$")
        return ip_pattern.match(value) or hostname_pattern.match(value)
