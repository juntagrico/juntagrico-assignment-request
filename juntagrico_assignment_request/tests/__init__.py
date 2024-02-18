from django.contrib.auth.models import Permission
from django.utils import timezone
from juntagrico.tests import JuntagricoTestCase

from juntagrico_assignment_request.models import AssignmentRequest


class AssignmentRequestTestCase(JuntagricoTestCase):
    @classmethod
    def setUpTestData(cls):
        # load from fixtures
        cls.load_members()
        cls.load_areas()
        cls.set_up_approvers()

    @classmethod
    def set_up_approvers(cls):
        cls.approver = cls.create_member('approver@email.org')
        cls.approver2 = cls.create_member('approver2@email.org')
        cls.approver.user.user_permissions.add(
            Permission.objects.get(codename='can_confirm_assignments'))
        cls.approver.user.save()
        cls.approver2.user.user_permissions.add(
            Permission.objects.get(codename='can_confirm_assignments'))
        cls.approver2.user.user_permissions.add(
            Permission.objects.get(codename='notified_on_unapproved_assignments'))
        cls.approver2.user.save()

    @classmethod
    def assignment_request_data(cls, approver=None, for_form=False, approved=False, **kwargs):
        if for_form:
            if approver is None:
                approver = ''
            else:
                approver = approver.pk
        date = timezone.now()
        data = {
            'job_time': date.strftime('%Y-%m-%d %H:%M') if for_form else date,
            'duration': 4,
            'amount': 0.5,
            'approver': approver,
            'activityarea': cls.area.pk if for_form else cls.area,
            'location': 'location',
            'description': 'description'
        }
        data.update(**kwargs)
        if not for_form:
            data['member'] = cls.member
            if approved:
                data['status'] = AssignmentRequest.CONFIRMED
        return data

    @classmethod
    def assignment_response_data(cls, decision='submit'):
        """
        :param decision: ['confirm', 'reject', 'submit'(default)]
        """
        return {
            'response': 'response',
            decision: True,
            'amount': 2,
            'duration': 5,
            'activityarea': cls.area.pk,
            'location': 'location'
        }
