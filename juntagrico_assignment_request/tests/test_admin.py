from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone

from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


class AdminTests(AssignmentRequestTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # staff member, that can edit requests but is no approver
        cls.staff = cls.create_member('staff@email.org')
        cls.staff.user.is_staff = True
        cls.staff.user.save()
        cls.staff.user.user_permissions.add(
            *Permission.objects.filter(codename__in=['view_assignmentrequest', 'change_assignmentrequest']))

    def change_url(self, ar):
        return reverse('admin:juntagrico_assignment_request_assignmentrequest_change', args=(ar.pk,))

    def admin_data(self, ar, **kwargs):
        job_time = timezone.localtime(ar.job_time)
        data = {
            'member': ar.member.pk,
            'amount': ar.amount,
            'job_time_0': job_time.strftime('%d.%m.%Y'),
            'job_time_1': job_time.strftime('%H:%M:%S'),
            'request_date': ar.request_date.strftime('%d.%m.%Y'),
            'response_date': '',
            'approver': ar.approver.pk if ar.approver else '',
            'description': ar.description,
            'activityarea': ar.activityarea.pk,
            'duration': ar.duration,
            'location': ar.location,
            'status': ar.status,
            'response': '',
        }
        data.update(kwargs)
        return data

    def own_request(self, member, **kwargs):
        data = self.assignment_request_data(**kwargs)
        data['member'] = member
        return AssignmentRequest.objects.create(**data)

    def test_assignment_request_admin(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertGet(self.change_url(ar), member=self.admin)

    def test_admin_can_confirm_request(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertPost(self.change_url(ar), self.admin_data(ar, status=AssignmentRequest.CONFIRMED), 302,
                        member=self.admin)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)

    def test_admin_can_not_confirm_own_request(self):
        ar = self.own_request(self.admin)
        response = self.assertPost(self.change_url(ar), self.admin_data(ar, status=AssignmentRequest.CONFIRMED),
                                   member=self.admin)
        self.assertTrue(response.context['adminform'].form.non_field_errors())
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)

    def test_admin_can_not_change_own_confirmed_request(self):
        ar = self.own_request(self.admin, approved=True)
        self.assertPost(self.change_url(ar), self.admin_data(ar, amount=20), member=self.admin)
        ar.refresh_from_db()
        self.assertEqual(ar.amount, 0.5)

    def test_admin_can_change_own_pending_request(self):
        ar = self.own_request(self.admin)
        self.assertPost(self.change_url(ar), self.admin_data(ar, description='changed'), 302, member=self.admin)
        ar.refresh_from_db()
        self.assertEqual(ar.description, 'changed')

    def test_staff_without_approver_permission_can_not_confirm(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        response = self.assertGet(self.change_url(ar), member=self.staff)
        self.assertNotIn('status', response.context['adminform'].form.fields)
        self.assertContains(response, 'Beantragt')
        self.assertNotContains(response, 'um die Anfrage anzunehmen')
        self.assertPost(self.change_url(ar), self.admin_data(ar, status=AssignmentRequest.CONFIRMED,
                                                             description='changed'), 302, member=self.staff)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(ar.description, 'changed')
