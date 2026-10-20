from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from juntagrico.admins import BaseAdmin

from juntagrico_assignment_request.models import AssignmentRequest
from juntagrico_assignment_request.utils import get_approvers


class AssignmentRequestAdminForm(ModelForm):
    class Meta:
        model = AssignmentRequest
        fields = '__all__'

    # set by AssignmentRequestAdmin.get_form
    approver_member = None

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['approver'].queryset = get_approvers()

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        if member is not None and member == self.approver_member and self.changed_data:
            # nobody can confirm their own requests or change them once confirmed
            confirmed = AssignmentRequest.CONFIRMED
            if cleaned_data.get('status', self.instance.status) == confirmed and \
                    ('status' in self.changed_data or self.instance.status == confirmed):
                raise ValidationError(_('Du kannst deine eigene Anfrage nicht bestätigen '
                                        'oder nach der Bestätigung ändern.'))
        return cleaned_data


class AssignmentRequestAdmin(BaseAdmin):
    form = AssignmentRequestAdminForm
    raw_id_fields = ['member']
    list_display = ['member', 'amount', 'job_time', 'duration', 'activityarea',
                    'location', 'request_date', 'approver', 'status', ]
    readonly_fields = ['assignment']

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.has_perm('juntagrico_assignment_request.can_confirm_assignments'):
            # only general approvers can respond to requests
            readonly_fields.append('status')
        return readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.approver_member = getattr(request.user, 'member', None)
        return form
