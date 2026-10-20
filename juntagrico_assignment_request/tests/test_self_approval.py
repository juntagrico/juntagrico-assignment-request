from django.core import mail
from django.urls import reverse

from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


class SelfApprovalTests(AssignmentRequestTestCase):
    def own_request(self, member, approver=None):
        data = self.assignment_request_data(approver, amount=50)
        data['member'] = member
        return AssignmentRequest.objects.create(**data)

    def assertNotConfirmable(self, ar, member):
        self.assertGet(reverse('juntagrico-assignment-request:confirm', args=(ar.pk,)), 302, member=member)
        self.assertGet(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)), 302, member=member)
        self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                        self.assignment_response_data('confirm'), 302, member=member)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertIsNone(ar.assignment)

    def test_general_approver_can_not_confirm_own_request(self):
        self.assertNotConfirmable(self.own_request(self.approver), self.approver)

    def test_general_approver_can_not_confirm_own_request_assigned_to_them(self):
        self.assertNotConfirmable(self.own_request(self.approver, approver=self.approver), self.approver)

    def test_area_approver_can_not_confirm_own_request(self):
        self.assertNotConfirmable(self.own_request(self.area_admin, approver=self.area_admin), self.area_admin)

    def test_other_approver_can_confirm(self):
        ar = self.own_request(self.approver)
        self.assertPost(reverse('juntagrico-assignment-request:confirm', args=(ar.pk,)), code=302, member=self.approver2)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)

    def test_own_request_not_listed(self):
        own = self.own_request(self.approver2)
        other = self.own_request(self.member)
        response = self.assertGet(reverse('juntagrico-assignment-request:list'), member=self.approver2)
        self.assertNotIn(own, response.context['assignment_requests'])
        self.assertIn(other, response.context['assignment_requests'])

    def test_own_member_not_selectable_as_approver(self):
        response = self.assertGet(reverse('juntagrico-assignment-request:request'), member=self.area_admin)
        approvers = response.context['form'].fields['approver'].queryset
        self.assertNotIn(self.area_admin, approvers)
        self.assertIn(self.approver, approvers)
        self.assertPost(reverse('juntagrico-assignment-request:request'),
                        self.assignment_request_data(self.area_admin, for_form=True), member=self.area_admin)
        self.assertFalse(AssignmentRequest.objects.filter(member=self.area_admin).exists())

    def test_requester_not_notified_about_own_request(self):
        self.assertPost(reverse('juntagrico-assignment-request:request'),
                        self.assignment_request_data(for_form=True), 302, member=self.approver2)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(self.approver2.email, mail.outbox[0].to)
