from django.contrib.auth.models import Permission
from django.core import mail
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils import timezone
from juntagrico.entity.jobs import ActivityArea
from juntagrico.entity.member import Member

from juntagrico_assignment_request.entity.assignment_request import AssignmentRequest


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AssignmentRequestTests(TestCase):

    def setUp(self):
        self.set_up_member()
        self.set_up_area()

    @staticmethod
    def create_member(email):
        member_data = {'first_name': 'first_name',
                       'last_name': 'last_name',
                       'email': email,
                       'addr_street': 'addr_street',
                       'addr_zipcode': 'addr_zipcode',
                       'addr_location': 'addr_location',
                       'phone': 'phone',
                       'confirmed': True,
                       }
        member = Member.objects.create(**member_data)
        member.user.set_password('12345')
        member.user.save()
        return member

    def assignment_request_data(self, approver=None, for_form=False):
        if for_form:
            if approver is None:
                approver = ''
            else:
                approver = approver.pk
        date = timezone.now()
        data = {
            'job_time': date.strftime('%Y-%m-%d %H:%M') if for_form else date,
            'duration': 4,
            'amount': 1,
            'approver': approver,
            'activityarea': self.area.pk if for_form else self.area,
            'location': 'location',
            'description': 'description'
        }
        if not for_form:
            data['member'] = self.member
        return data

    def set_up_member(self):
        """
        member
        """
        self.member = self.create_member('member@email.org')
        self.approver = self.create_member('approver@email.org')
        self.approver2 = self.create_member('approver2@email.org')
        self.approver.user.user_permissions.add(
            Permission.objects.get(codename='can_confirm_assignments'))
        self.approver.user.save()
        self.approver2.user.user_permissions.add(
            Permission.objects.get(codename='can_confirm_assignments'))
        self.approver2.user.user_permissions.add(
            Permission.objects.get(codename='notified_on_unapproved_assignments'))
        self.approver2.user.save()

    def set_up_area(self):
        """
        area
        """
        area_data = {'name': 'name',
                     'coordinator': self.approver}
        area_data2 = {'name': 'name2',
                      'coordinator': self.approver2,
                      'hidden': True}
        self.area = ActivityArea.objects.create(**area_data)
        self.area2 = ActivityArea.objects.create(**area_data2)

    def assertGet(self, url, code=200, member=None):
        login_member = member or self.member
        self.client.force_login(login_member.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, code)

    def assertPost(self, url, data=None, code=200, member=None):
        login_member = member or self.member
        self.client.force_login(login_member.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, code)

    def test_assignment_request(self):
        self.assertGet(reverse('ar-request-assignment'))
        self.assertPost(reverse('ar-request-assignment'),
                        self.assignment_request_data(self.approver, for_form=True), 302)
        ar = AssignmentRequest.objects.filter(approver=self.approver.pk)
        self.assertEqual(ar.count(), 1)
        self.assertEqual(ar.first().status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 1)  # request email to approver
        self.assertEqual(mail.outbox[0].to[0], self.approver.email)

    def test_assignment_request_edit(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertGet(reverse('ar-request-assignment'))  # test list of existing own requests
        self.assertGet(reverse('ar-edit-assignment-request', args=(ar.pk,)))
        self.assertPost(reverse('ar-edit-assignment-request', args=(ar.pk,)),
                        self.assignment_request_data(self.approver, for_form=True), 302)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 1)  # edit notification to approver
        self.assertEqual(mail.outbox[0].to[0], self.approver.email)

    def test_assignment_request_delete(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertGet(reverse('ar-delete-assignment-request', args=(ar.pk,)), 302)
        with self.assertRaises(AssignmentRequest.DoesNotExist):
            ar.refresh_from_db()

    def test_assignment_request_not_deletable(self):
        # can not delete accepted assignment request
        data = self.assignment_request_data(self.approver)
        data['status'] = AssignmentRequest.CONFIRMED
        ar = AssignmentRequest.objects.create(**data)
        self.assertGet(reverse('ar-delete-assignment-request', args=(ar.pk,)), 302)
        ar.refresh_from_db()
        self.assertNotEquals(ar, None)

    def test_assignment_request_wo_approver(self):
        self.assertPost(reverse('ar-request-assignment'), self.assignment_request_data(for_form=True), 302)
        ar = AssignmentRequest.objects.filter(approver=self.approver.pk)
        self.assertEqual(ar.count(), 0)
        self.assertEqual(len(mail.outbox), 1)  # request email to general approver
        self.assertEqual(mail.outbox[0].to[0], self.approver2.email)

    def test_assignment_request_list(self):
        AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))  # display at least one ar
        self.assertGet(reverse('ar-list-assignment-requests'), 302)  # normal member has no access
        self.assertGet(reverse('ar-list-assignment-requests'), member=self.approver)

    def test_assignment_confirmation(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertGet(reverse('ar-confirm-assignment-request', args=(ar.pk,)), 302)  # member can not approve
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertGet(reverse('ar-confirm-assignment-request', args=(ar.pk,)), 302, member=self.approver)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)
        self.assertEqual(len(mail.outbox), 1)  # confirmation email to user
        self.assertEqual(mail.outbox[0].to[0], self.member.email)

    def test_assignment_confirmation_with_response_by_other_approver(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertGet(reverse('ar-respond-assignment-request', args=(ar.pk,)), member=self.approver)
        data = {
            'response': 'response',
            'confirm': True,
            'amount': 2,
            'activityarea': self.area.pk,
            'location': 'location'
        }
        self.assertPost(reverse('ar-respond-assignment-request', args=(ar.pk,)), data, 302, member=self.approver2)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)
        self.assertEqual(ar.approver, self.approver2)  # approver changed to actual approver
        self.assertEqual(len(mail.outbox), 2)  # rejection email to user and information to original approver
        self.assertEqual(mail.outbox[0].to[0], self.approver.email)
        self.assertEqual(mail.outbox[1].to[0], self.member.email)

    def test_assignment_reply(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        data = {
            'response': 'response',
            'submit': True,  # just a reply
            'amount': 2,
            'activityarea': self.area.pk,
            'location': 'location'
        }
        self.assertPost(reverse('ar-respond-assignment-request', args=(ar.pk,)), data, 302, member=self.approver)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 1)  # rejection email to user
        self.assertEqual(mail.outbox[0].to[0], self.member.email)

    def test_assignment_rejection(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        data = {
            'response': 'response',
            'reject': True,
            'amount': 2,
            'activityarea': self.area.pk,
            'location': 'location'
        }
        self.assertPost(reverse('ar-respond-assignment-request', args=(ar.pk,)), data, 302, member=self.approver)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REJECTED)
        self.assertEqual(len(mail.outbox), 1)  # rejection email to user
        self.assertEqual(mail.outbox[0].to[0], self.member.email)
