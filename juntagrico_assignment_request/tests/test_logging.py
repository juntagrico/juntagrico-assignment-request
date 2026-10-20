from contextlib import redirect_stdout
from io import StringIO

from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


class LoggingTests(AssignmentRequestTestCase):
    def test_no_personal_data_on_stdout(self):
        stdout = StringIO()
        with redirect_stdout(stdout), self.assertLogs('juntagrico_assignment_request.hack', 'DEBUG') as logs:
            ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, approved=True))
            ar.assignment.job.save()  # triggers re-saving the request
        self.assertEqual(stdout.getvalue(), '')
        output = '\n'.join(logs.output)
        self.assertIn(f'assignment request {ar.pk}', output)
        self.assertNotIn(str(self.member), output)
