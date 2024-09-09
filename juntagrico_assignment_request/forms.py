from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import ModelForm, DateTimeInput
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext
from django.urls import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML
from crispy_forms.bootstrap import FormActions

from juntagrico_assignment_request.models import AssignmentRequest
from juntagrico_assignment_request.utils import get_approvers


class DateTimeWidget(DateTimeInput):
    """ Widget using browsers date picker
    """
    input_type = 'datetime-local'

    def format_value(self, value):
        if isinstance(value, str):
            return value
        return value.strftime('%Y-%m-%dT%H:%M')


class AssignmentRequestForm(ModelForm):
    class Meta:
        model = AssignmentRequest
        fields = ('job_time', 'amount', 'duration', 'activityarea',
                  'approver', 'location', 'description')
        labels = {
            "amount": _("Anzahl Einsätze"),
            "approver": _("Abgesprochen mit"),
            "activityarea": _("Tätigkeitsbereich"),
        }

    def activityarea_queryset(self):
        qs = self.fields['activityarea'].queryset
        qs_filter = getattr(settings, 'ASSIGNMENT_REQUEST_AREAS', None)
        if callable(qs_filter):
            return qs_filter(qs)
        return qs

    def approvers_by_area(self):
        area_approvers = get_approvers(area_only=True)
        approvers = {
            approver.id: [area.id for area in approver.activityarea_set.filter(pk__in=self.fields['activityarea'].queryset)]
            for approver in area_approvers
        }
        return approvers

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['approver'].queryset = get_approvers()
        self.fields['activityarea'].queryset = self.activityarea_queryset()
        self.fields['duration'].widget.attrs['step'] = 'any'
        self.fields['job_time'].widget = DateTimeWidget()
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            'job_time', 'amount', 'duration', 'activityarea',
            'approver', 'location', 'description',
            FormActions(
                Submit('submit', _('Absenden'), css_class='btn-success'),
            )
        )

    def clean(self):
        # check that approver is valid for the selected area
        cleaned_data = super().clean()
        valid_approvers = (get_approvers(general_only=True) |
                           get_approvers().filter(activityarea=cleaned_data['activityarea']))
        if cleaned_data['approver'] and cleaned_data['approver'] not in valid_approvers:
            raise ValidationError(_('Ungültige Auswahl bei "Abgesprochen mit"'))


class AssignmentResponseForm(ModelForm):
    class Meta:
        model = AssignmentRequest
        fields = ('amount', 'duration', 'activityarea', 'location', 'response')
        labels = {
            "amount": _("Anzahl Einsätze"),
            "activityarea": _("Tätigkeitsbereich"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['duration'].widget.attrs['step'] = 'any'
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            'amount', 'duration', 'activityarea', 'location', 'response',
            FormActions(
                Submit('confirm', _('Bestätigen'), css_class='btn-success'),
                Submit('reject', _('Ablehnen'), css_class='btn-danger'),
                Submit('submit', _('Nur Antwort senden'), css_class='btn-warning'),
                HTML('<a href="' + reverse('juntagrico-assignment-request:list') + '" class="btn">' + gettext("Abbrechen") + '</a>'),
            )
        )
