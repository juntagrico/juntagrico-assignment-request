from datetime import date, timedelta

from django.core import mail
from django.test import override_settings
from django.urls import reverse

from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


class MaxPendingTests(AssignmentRequestTestCase):
    def create_requests(self, count, request_date=None, **kwargs):
        # requests of previous days by default, so that they do not count for the daily limit
        request_date = request_date or date.today() - timedelta(days=1)
        for _ in range(count):
            AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, request_date=request_date,
                                                                            **kwargs))

    def post_request(self, code=302):
        return self.assertPost(reverse('juntagrico-assignment-request:request'),
                               self.assignment_request_data(self.approver, for_form=True), code)

    def post_edit(self, ar, code=302, **kwargs):
        return self.assertPost(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)),
                               self.assignment_request_data(self.approver, for_form=True, **kwargs), code)

    def test_default_limit(self):
        self.create_requests(49)
        self.post_request()
        response = self.post_request(200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertEqual(AssignmentRequest.objects.count(), 50)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(ASSIGNMENT_REQUEST_MAX_PENDING=1)
    def test_form_hidden_at_limit(self):
        url = reverse('juntagrico-assignment-request:request')
        response = self.assertGet(url)
        self.assertIsNone(response.context['limit_error'])
        self.assertContains(response, 'id="request_assignment"')
        self.create_requests(1)
        response = self.assertGet(url)
        self.assertTrue(response.context['limit_error'])
        self.assertNotContains(response, 'id="request_assignment"')

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
        self.post_edit(ar, description='changed')

    @override_settings(ASSIGNMENT_REQUEST_MAX_PENDING=None, ASSIGNMENT_REQUEST_MAX_PER_DAY=None)
    def test_no_limit(self):
        self.create_requests(20, request_date=date.today())
        self.post_request()

    @override_settings(ASSIGNMENT_REQUEST_MAX_PER_DAY=2)
    def test_daily_limit(self):
        self.create_requests(5)
        self.create_requests(1, request_date=date.today(), status=AssignmentRequest.REJECTED)
        self.post_request()
        response = self.post_request(200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(ASSIGNMENT_REQUEST_MAX_PER_DAY=1)
    def test_daily_limit_on_rerequest(self):
        self.create_requests(2)
        ar1, ar2 = AssignmentRequest.objects.all()
        self.post_edit(ar1, amount=1)
        ar1.refresh_from_db()
        self.assertEqual(ar1.request_date, date.today())
        self.assertEqual(len(mail.outbox), 1)
        # editing another request that would need another approval is not possible anymore today
        self.post_edit(ar2, 200, amount=1)
        # changes that do not need another approval are still possible
        self.post_edit(ar2, description='changed')
        self.assertEqual(len(mail.outbox), 1)

    def test_one_notification_per_request_and_day(self):
        self.create_requests(1)
        ar = AssignmentRequest.objects.get()
        for amount in (1, 2, 3):
            self.post_edit(ar, amount=amount)
        ar.refresh_from_db()
        self.assertEqual(ar.amount, 3)
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 1)

    def test_rejected_request_notifies_again_on_same_day(self):
        self.create_requests(1, request_date=date.today(), status=AssignmentRequest.REJECTED)
        ar = AssignmentRequest.objects.get()
        self.post_edit(ar, amount=1)
        self.assertEqual(len(mail.outbox), 1)
