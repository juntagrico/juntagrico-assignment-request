from datetime import datetime, timedelta

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from juntagrico.util.temporal import start_of_business_year

from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


def fmt(time):
    # format as the browser does, i.e. in local time
    if timezone.is_aware(time):
        time = timezone.localtime(time)
    return time.strftime('%Y-%m-%d %H:%M')


class EditRestrictionTests(AssignmentRequestTestCase):
    def test_confirmed_request_can_not_be_edited(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, approved=True))
        job = ar.assignment.job
        self.assertGet(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)), 302)
        last_year = timezone.now() - timedelta(days=400)
        self.assertPost(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)),
                        self.assignment_request_data(self.approver, for_form=True, amount=0.1,
                                                     description='changed',
                                                     job_time=fmt(last_year)), 302)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)
        self.assertEqual(ar.description, 'description')
        self.assertEqual(ar.amount, 0.5)
        self.assertEqual(ar.assignment.job, job)

    def test_confirmed_request_has_no_edit_link(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, approved=True))
        response = self.assertGet(reverse('juntagrico-assignment-request:request'))
        self.assertNotContains(response, reverse('juntagrico-assignment-request:edit', args=(ar.pk,)))

    def assertJobTimeValid(self, job_time):
        self.assertPost(reverse('juntagrico-assignment-request:request'),
                        self.assignment_request_data(for_form=True, job_time=fmt(job_time)), 302)
        self.assertTrue(AssignmentRequest.objects.exists())

    def assertJobTimeInvalid(self, job_time):
        response = self.assertPost(reverse('juntagrico-assignment-request:request'),
                                   self.assignment_request_data(for_form=True,
                                                                job_time=fmt(job_time)))
        self.assertIn('job_time', response.context['form'].errors)
        self.assertFalse(AssignmentRequest.objects.exists())

    def test_job_time_in_future(self):
        self.assertJobTimeInvalid(timezone.now() + timedelta(hours=1))

    def test_job_time_without_grace_period(self):
        # default: any date in the past is allowed
        self.assertJobTimeValid(timezone.now() - timedelta(days=400))

    @override_settings(ASSIGNMENT_REQUEST_GRACE_PERIOD=0)
    def test_job_time_before_business_year(self):
        start = datetime.combine(start_of_business_year(), datetime.min.time())
        self.assertJobTimeInvalid(start - timedelta(minutes=1))

    @override_settings(ASSIGNMENT_REQUEST_GRACE_PERIOD=0)
    def test_job_time_at_start_of_business_year(self):
        self.assertJobTimeValid(datetime.combine(start_of_business_year(), datetime.min.time()))

    def grace_period_into_last_year(self):
        # grace period that reaches exactly one day into the last business year
        return (timezone.localdate() - start_of_business_year()).days + 1

    def test_job_time_within_grace_period(self):
        with self.settings(ASSIGNMENT_REQUEST_GRACE_PERIOD=self.grace_period_into_last_year()):
            start = datetime.combine(start_of_business_year(), datetime.min.time())
            self.assertJobTimeValid(start - timedelta(days=1))

    def test_job_time_before_grace_period(self):
        with self.settings(ASSIGNMENT_REQUEST_GRACE_PERIOD=self.grace_period_into_last_year()):
            start = datetime.combine(start_of_business_year(), datetime.min.time())
            self.assertJobTimeInvalid(start - timedelta(days=1, minutes=1))

    @override_settings(ASSIGNMENT_REQUEST_GRACE_PERIOD=0)
    def test_old_job_time_of_pending_request_can_be_kept(self):
        last_year = timezone.now() - timedelta(days=400)
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, job_time=last_year))
        self.assertPost(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)),
                        self.assignment_request_data(self.approver, for_form=True, description='changed',
                                                     job_time=fmt(last_year)),
                        302)
        ar.refresh_from_db()
        self.assertEqual(ar.description, 'changed')

    @override_settings(ASSIGNMENT_REQUEST_GRACE_PERIOD=0)
    def test_job_time_of_pending_request_can_not_be_moved_to_last_year(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        last_year = timezone.now() - timedelta(days=400)
        response = self.assertPost(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)),
                                   self.assignment_request_data(self.approver, for_form=True,
                                                                job_time=fmt(last_year)))
        self.assertIn('job_time', response.context['form'].errors)
