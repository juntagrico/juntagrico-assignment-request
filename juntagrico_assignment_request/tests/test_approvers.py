from . import AssignmentRequestTestCase
from ..utils import get_approvers


class AdminTests(AssignmentRequestTestCase):
    def test_get_approvers(self):
        approvers = get_approvers()
        self.assertQuerysetEqual(approvers, [self.approver, self.approver2, self.area_admin],
                                 ordered=False)
        genenral_approvers = get_approvers(general_only=True)
        self.assertQuerysetEqual(genenral_approvers, [self.approver, self.approver2], ordered=False)
        area_approvers = get_approvers(area_only=True)
        self.assertQuerysetEqual(area_approvers, [self.area_admin], ordered=False)
