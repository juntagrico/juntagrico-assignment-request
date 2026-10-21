from datetime import date, timedelta

from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.forms import ModelForm, DateTimeInput
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext
from django.urls import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML
from crispy_forms.bootstrap import FormActions

from juntagrico.util.temporal import start_of_business_year

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
            approver.id: [area.id for area in approver.coordinated_areas.filter(pk__in=self.fields['activityarea'].queryset)]
            for approver in area_approvers
        }
        return approvers

    def __init__(self, *args, member=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.member = member
        # values before editing, to detect changes that need another approval
        self.old_amount = self.instance.get_amount() if self.instance.pk else None
        self.old_request_date = self.instance.request_date
        self.old_status = self.instance.status
        approvers = get_approvers()
        if member is not None:
            # members can not approve their own requests
            approvers = approvers.exclude(pk=member.pk)
        self.fields['approver'].queryset = approvers
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

    def clean_job_time(self):
        job_time = self.cleaned_data['job_time']
        old_job_time = self.instance.job_time if self.instance.pk else None
        if old_job_time and job_time.replace(second=0, microsecond=0) == old_job_time.replace(second=0, microsecond=0):
            # keep date of existing requests, even if it would not be valid anymore
            return job_time
        if job_time > timezone.now():
            raise ValidationError(_('Das Datum darf nicht in der Zukunft liegen.'))
        earliest = self.earliest_job_date()
        if earliest and timezone.localtime(job_time).date() < earliest:
            raise ValidationError(_('Das Datum darf nicht vor dem {} liegen.').format(date_format(earliest)))
        return job_time

    @staticmethod
    def earliest_job_date():
        # None: no limit. Otherwise, the current business year and the given number of days before today are allowed
        grace_period = getattr(settings, 'ASSIGNMENT_REQUEST_GRACE_PERIOD', None)
        if grace_period is None:
            return None
        return min(start_of_business_year(), timezone.localdate() - timedelta(days=grace_period))

    def clean(self):
        # check that approver is valid for the selected area
        cleaned_data = super().clean()
        # fields are missing in cleaned_data, if their own validation failed already
        approver = cleaned_data.get('approver')
        if approver and 'activityarea' in cleaned_data:
            valid_approvers = (get_approvers(general_only=True) |
                               get_approvers().filter(coordinated_areas=cleaned_data['activityarea']))
            if approver not in valid_approvers:
                raise ValidationError(_('Ungültige Auswahl bei "Abgesprochen mit"'))
        error = self.limit_error()
        if error:
            raise ValidationError(error)
        return cleaned_data

    def amount_increased(self):
        # an edited request with a higher amount must be approved again
        if self.old_amount is None:
            return False
        amount = self.cleaned_data.get('amount')
        duration = self.cleaned_data.get('duration')
        if amount is None or duration is None:
            return False
        return AssignmentRequest(amount=amount, duration=duration).get_amount() > self.old_amount

    def sends_notification(self):
        # approvers are notified at most once per day about the same pending request
        if self.instance.pk is None:
            return True
        notified_today = self.old_status == AssignmentRequest.REQUESTED and self.old_request_date == date.today()
        return self.amount_increased() and not notified_today

    def limit_error(self):
        # limit number of requests, as each request sends emails to the approvers
        if self.instance.pk:
            return self.max_per_day_error() if self.sends_notification() else None
        return self.new_request_limit_error()

    def new_request_limit_error(self):
        """
        :return: error message, if the member can not create another request
        """
        if self.member is None:
            return None
        max_pending = getattr(settings, 'ASSIGNMENT_REQUEST_MAX_PENDING', 50)
        if max_pending is not None:
            pending = AssignmentRequest.objects.filter(member=self.member, status=AssignmentRequest.REQUESTED)
            if pending.count() >= max_pending:
                return gettext('Du hast bereits %(count)s offene Anfragen. '
                               'Bitte warte, bis diese beantwortet sind.') % {'count': max_pending}
        return self.max_per_day_error()

    def max_per_day_error(self):
        """
        :return: error message, if the member sent the maximum number of requests today
        """
        max_per_day = getattr(settings, 'ASSIGNMENT_REQUEST_MAX_PER_DAY', 20)
        if max_per_day is None or self.member is None:
            return None
        sent_today = AssignmentRequest.objects.filter(member=self.member, request_date=date.today())
        if self.instance.pk:
            sent_today = sent_today.exclude(pk=self.instance.pk)
        if sent_today.count() >= max_per_day:
            return gettext('Du hast heute bereits %(count)s Anfragen gesendet. '
                           'Bitte versuche es morgen wieder.') % {'count': max_per_day}
        return None


class AssignmentResponseForm(ModelForm):
    class Meta:
        model = AssignmentRequest
        fields = ('amount', 'duration', 'activityarea', 'location', 'response')
        labels = {
            "amount": _("Anzahl Einsätze"),
            "activityarea": _("Tätigkeitsbereich"),
        }

    def __init__(self, *args, areas=None, **kwargs):
        """
        :param areas: if set, the activity area can only be changed to one of these areas
        """
        super().__init__(*args, **kwargs)
        if areas is not None:
            # keep the current area selectable, e.g. if the coordinator changed in the meantime
            self.fields['activityarea'].queryset = self.fields['activityarea'].queryset.filter(
                Q(pk__in=areas) | Q(pk=self.instance.activityarea_id))
            self.fields['activityarea'].required = True
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
