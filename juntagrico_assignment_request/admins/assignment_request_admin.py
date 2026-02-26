from django.forms import ModelForm

from juntagrico.admins import BaseAdmin

from juntagrico_assignment_request.models import AssignmentRequest
from juntagrico_assignment_request.utils import get_approvers


class AssignmentRequestAdminForm(ModelForm):
    class Meta:
        model = AssignmentRequest
        fields = '__all__'

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['approver'].queryset = get_approvers()


class AssignmentRequestAdmin(BaseAdmin):
    form = AssignmentRequestAdminForm
    raw_id_fields = ['member']
    list_display = ['member', 'amount', 'job_time', 'duration', 'activityarea',
                    'location', 'request_date', 'approver', 'status', ]
    readonly_fields = ['assignment']
