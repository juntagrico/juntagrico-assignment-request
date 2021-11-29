from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext
from django.urls import reverse

from juntagrico_assignment_request.dao.assignmentrequestdao import AssignmentRequestDao
from juntagrico_assignment_request.models import AssignmentRequest

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML
from crispy_forms.bootstrap import FormActions


class AssignmentRequestForm(ModelForm):
    class Meta:
        model = AssignmentRequest
        fields = ('job_time', 'amount', 'duration', 'approver',
                  'activityarea', 'location', 'description')
        labels = {
            "amount": _("Anzahl Einsätze"),
            "approver": _("Abgesprochen mit"),
            "activityarea": _("Tätigkeitsbereich"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['approver'].queryset = AssignmentRequestDao.all_approvers()
        self.fields['amount'].widget.attrs['min'] = 1
        self.fields['job_time'].widget.format = '%d.%m.%Y %H:%M'
        self.fields['job_time'].widget.attrs['placeholder'] = _('TT.MM.JJJJ HH:MM')
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            'job_time', 'amount', 'duration', 'approver',
            'activityarea', 'location', 'description',
            FormActions(
                Submit('submit', _('Absenden'), css_class='btn-success'),
            )
        )


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
        self.fields['amount'].widget.attrs['min'] = 1
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
                HTML('<a href="' + reverse('ar-list-assignment-requests') + '" class="btn">' + gettext("Abbrechen") + '</a>'),
            )
        )
