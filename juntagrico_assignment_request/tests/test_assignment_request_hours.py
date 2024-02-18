from django.test import override_settings

from .test_assignment_request import AssignmentRequestTests


@override_settings(ASSIGNMENT_UNIT='HOURS')
class AssignmentRequestHoursTests(AssignmentRequestTests):
    pass
