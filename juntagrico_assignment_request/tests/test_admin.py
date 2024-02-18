from django.urls import reverse

from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


class AdminTests(AssignmentRequestTestCase):

    def test_assignment_request_admin(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertGet(reverse('admin:juntagrico_assignment_request_assignmentrequest_change', args=(ar.pk,)),
                       member=self.admin)
