from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


class ManipulationTests(AssignmentRequestTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ar = AssignmentRequest.objects.create(**cls.assignment_request_data(cls.approver, approved=True))

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
        self.assertEqual(self.ar.assignment.amount, 0.5)
