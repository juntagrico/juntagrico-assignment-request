from django.core import mail
from django.urls import reverse

from juntagrico_assignment_request.entity.assignment_request import AssignmentRequest
from test import AssignmentRequestTestCase


class AssignmentRequestTests(AssignmentRequestTestCase):
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
        data = self.assignment_request_data(self.approver, approved=True)
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

    def test_assignment_request_archive(self):
        AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))  # display at least one ar
        self.assertGet(reverse('ar-list-archive'), 302)  # normal member has no access
        self.assertGet(reverse('ar-list-archive'), member=self.approver)

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
        self.assertPost(reverse('ar-respond-assignment-request', args=(ar.pk,)),
                        self.assignment_response_data('confirm'), 302, member=self.approver2)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)
        self.assertEqual(ar.approver, self.approver2)  # approver changed to actual approver
        self.assertEqual(len(mail.outbox), 2)  # rejection email to user and information to original approver
        self.assertEqual(mail.outbox[0].to[0], self.approver.email)
        self.assertEqual(mail.outbox[1].to[0], self.member.email)

    def assignment_response(self, decision='submit', expected_status=AssignmentRequest.REQUESTED):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertPost(reverse('ar-respond-assignment-request', args=(ar.pk,)),
                        self.assignment_response_data(decision), 302, member=self.approver)
        ar.refresh_from_db()
        self.assertEqual(ar.status, expected_status)
        self.assertEqual(len(mail.outbox), 1)  # reply email to user
        self.assertEqual(mail.outbox[0].to[0], self.member.email)

    def test_assignment_reply(self):
        self.assignment_response()

    def test_assignment_rejection(self):
        self.assignment_response('reject', AssignmentRequest.REJECTED)
