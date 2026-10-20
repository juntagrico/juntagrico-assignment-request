from django.urls import reverse

from juntagrico.entity.jobs import ActivityArea

from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


class AreaApproverResponseTests(AssignmentRequestTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.other_area = ActivityArea.objects.create(name='other area')

    def response_data(self, area, decision='confirm'):
        data = self.assignment_response_data(decision)
        data['activityarea'] = area.pk if area else ''
        return data

    def test_area_approver_can_only_select_own_areas(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.area_admin))
        response = self.assertGet(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)), member=self.area_admin)
        areas = response.context['form'].fields['activityarea'].queryset
        self.assertIn(self.area, areas)
        self.assertNotIn(self.other_area, areas)

    def test_area_approver_can_not_move_request_to_other_area(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.area_admin))
        response = self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                                   self.response_data(self.other_area), member=self.area_admin)
        self.assertIn('activityarea', response.context['form'].errors)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(ar.activityarea, self.area)

    def test_area_approver_must_select_area(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.area_admin))
        response = self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                                   self.response_data(None), member=self.area_admin)
        self.assertIn('activityarea', response.context['form'].errors)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)

    def test_area_approver_can_keep_current_area(self):
        # e.g. if the coordinator of the area changed after the request was sent
        ar = AssignmentRequest.objects.create(
            **self.assignment_request_data(self.area_admin, activityarea=self.other_area))
        self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                        self.response_data(self.other_area), 302, member=self.area_admin)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)
        self.assertEqual(ar.activityarea, self.other_area)

    def test_general_approver_can_select_any_area(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                        self.response_data(self.other_area), 302, member=self.approver)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)
        self.assertEqual(ar.activityarea, self.other_area)
