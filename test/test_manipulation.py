from juntagrico_assignment_request.entity.assignment_request import AssignmentRequest
from test import AssignmentRequestTestCase


class ManipulationTests(AssignmentRequestTestCase):
    def setUp(self):
        super().setUp()
        self.ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, approved=True))

    def test_job_type_manipulation(self):
        self.ar.assignment.job.type.activityarea = self.area2
        self.ar.save()
        self.assertEqual(self.ar.assignment.job.type.activityarea, self.area)

    def test_job_manipulation(self):
        self.ar.assignment.job.multiplier = 2
        self.ar.save()
        self.assertEqual(self.ar.assignment.job.multiplier, 1)

    def test_assignment_manipulation(self):
        self.ar.assignment.amount = 2
        self.ar.save()
        self.assertEqual(self.ar.assignment.amount, 1)
