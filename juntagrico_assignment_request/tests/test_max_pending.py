from django.core import mail
from django.test import override_settings
from django.urls import reverse

from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


class MaxPendingTests(AssignmentRequestTestCase):
    def create_requests(self, count, **kwargs):
        for _ in range(count):
            AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, **kwargs))

    def post_request(self, code=302):
        return self.assertPost(reverse('juntagrico-assignment-request:request'),
                               self.assignment_request_data(self.approver, for_form=True), code)

    def test_default_limit(self):
        self.create_requests(9)
        self.post_request()
        response = self.post_request(200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertEqual(AssignmentRequest.objects.count(), 10)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(ASSIGNMENT_REQUEST_MAX_PENDING=2)
    def test_answered_requests_do_not_count(self):
        self.create_requests(5, approved=True)
        self.create_requests(1, status=AssignmentRequest.REJECTED)
        self.create_requests(1)
        self.post_request()
        self.post_request(200)

    @override_settings(ASSIGNMENT_REQUEST_MAX_PENDING=2)
    def test_requests_of_others_do_not_count(self):
        for _ in range(2):
            data = self.assignment_request_data(self.approver)
            data['member'] = self.member2
            AssignmentRequest.objects.create(**data)
        self.post_request()

    @override_settings(ASSIGNMENT_REQUEST_MAX_PENDING=1)
    def test_pending_request_can_be_edited_at_limit(self):
        self.create_requests(1)
        ar = AssignmentRequest.objects.get()
        self.assertPost(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)),
                        self.assignment_request_data(self.approver, for_form=True, description='changed'), 302)

    @override_settings(ASSIGNMENT_REQUEST_MAX_PENDING=None)
    def test_no_limit(self):
        self.create_requests(20)
        self.post_request()
