from django.forms import ModelForm, URLField
from django.urls import reverse

from juntagrico.admins import BaseAdmin
from juntagrico.util.admin import MyHTMLWidget
from juntagrico.config import Config

from juntagrico_assignment_request.models import AssignmentRequest
from juntagrico_assignment_request.utils import get_approvers


class AssignmentRequestAdminForm(ModelForm):
    class Meta:
        model = AssignmentRequest
        fields = '__all__'

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.fields['approver'].queryset = get_approvers()
        instance = k.get('instance')
        self.fields['assignment_link'].initial = self.get_assignment_link(instance)

    @staticmethod
    def get_assignment_link(instance):
        if instance is None:
            return ''
        elif instance.assignment:
            return '<a href={}>{}</a>'.format(
                reverse('admin:juntagrico_assignment_change', args=(instance.assignment.id,)),
                instance.assignment
            )
        else:
            return '-'

    assignment_link = URLField(widget=MyHTMLWidget(), required=False, label=Config.vocabulary('assignment'))


class AssignmentRequestAdmin(BaseAdmin):
    form = AssignmentRequestAdminForm
    raw_id_fields = ['member']
    list_display = ['member', 'amount', 'job_time', 'duration', 'activityarea',
                    'location', 'request_date', 'approver', 'status', ]
    exclude = ('assignment',)
