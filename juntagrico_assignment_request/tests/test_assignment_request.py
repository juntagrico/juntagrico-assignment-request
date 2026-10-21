from django.core import mail
from django.urls import reverse

from juntagrico_assignment_request.models import AssignmentRequest
from . import AssignmentRequestTestCase


class AssignmentRequestTests(AssignmentRequestTestCase):
    @staticmethod
    def confirm_url(ar, key=None):
        url = reverse('juntagrico-assignment-request:confirm', args=(ar.pk,))
        return f'{url}?key={ar.confirm_key if key is None else key}'

    def test_assignment_request(self):
        self.assertGet(reverse('juntagrico-assignment-request:request'))
        self.assertPost(reverse('juntagrico-assignment-request:request'),
                        self.assignment_request_data(self.approver, for_form=True), 302)
        ar = AssignmentRequest.objects.filter(approver=self.approver.pk)
        self.assertEqual(ar.count(), 1)
        self.assertEqual(ar.first().status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 1)  # request email to approver
        self.assertEqual(mail.outbox[0].to[0], self.approver.email)

    def test_assignment_request_edit(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, status=AssignmentRequest.REJECTED))
        self.assertGet(reverse('juntagrico-assignment-request:request'))  # test list of existing own requests
        self.assertGet(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)))
        self.assertPost(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)),
                        self.assignment_request_data(self.approver, for_form=True, description='changed'), 302)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REJECTED)
        self.assertEqual(ar.description, 'changed')
        self.assertEqual(len(mail.outbox), 0)  # no notification to approver, because no re-approval needed.

    def test_assignment_request_edit_with_reapproval(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, status=AssignmentRequest.REJECTED))
        self.assertGet(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)))
        self.assertPost(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)),
                        self.assignment_request_data(self.approver, for_form=True, amount=2), 302)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 1)  # edit notification to approver
        self.assertEqual(mail.outbox[0].to[0], self.approver.email)

    def test_assignment_request_delete(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertPost(reverse('juntagrico-assignment-request:delete', args=(ar.pk,)), code=302)
        with self.assertRaises(AssignmentRequest.DoesNotExist):
            ar.refresh_from_db()

    def test_assignment_request_delete_link_shows_confirmation(self):
        # GET, e.g. the link in the rejection email, must not delete the request
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertGet(reverse('juntagrico-assignment-request:delete', args=(ar.pk,)))
        ar.refresh_from_db()

    def test_assignment_request_not_deletable(self):
        # can not delete accepted assignment request
        data = self.assignment_request_data(self.approver, approved=True)
        ar = AssignmentRequest.objects.create(**data)
        self.assertGet(reverse('juntagrico-assignment-request:delete', args=(ar.pk,)), 302)
        self.assertPost(reverse('juntagrico-assignment-request:delete', args=(ar.pk,)), code=302)
        ar.refresh_from_db()
        self.assertNotEqual(ar, None)

    def test_assignment_request_of_other_member_not_deletable(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertGet(reverse('juntagrico-assignment-request:delete', args=(ar.pk,)), 302, member=self.member2)
        self.assertPost(reverse('juntagrico-assignment-request:delete', args=(ar.pk,)), code=302, member=self.member2)
        ar.refresh_from_db()

    def test_assignment_request_wo_approver(self):
        self.assertPost(reverse('juntagrico-assignment-request:request'), self.assignment_request_data(for_form=True), 302)
        ar = AssignmentRequest.objects.filter(approver=self.approver.pk)
        self.assertEqual(ar.count(), 0)
        self.assertEqual(len(mail.outbox), 1)  # request email to general approver
        self.assertEqual(mail.outbox[0].to[0], self.approver2.email)

    def test_assignment_request_list(self):
        AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))  # display at least one ar
        self.assertGet(reverse('juntagrico-assignment-request:list'), 302)  # normal member has no access
        self.assertGet(reverse('juntagrico-assignment-request:list'), member=self.approver)
        self.assertGet(reverse('juntagrico-assignment-request:list'), member=self.area_admin)
        self.assertGet(reverse('juntagrico-assignment-request:list'), member=self.member2)

    def test_assignment_request_archive(self):
        AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))  # display at least one ar
        self.assertGet(reverse('juntagrico-assignment-request:archive'), 302)  # normal member has no access
        self.assertGet(reverse('juntagrico-assignment-request:archive'), member=self.approver)
        self.assertGet(reverse('juntagrico-assignment-request:archive'), member=self.area_admin)
        self.assertGet(reverse('juntagrico-assignment-request:archive'), member=self.member2)

    def test_assignment_confirmation(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        # normal member can not approve
        self.assertGet(self.confirm_url(ar), 302)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        # area approvers can not approve this request
        self.assertGet(self.confirm_url(ar), 302, member=self.member2)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertGet(self.confirm_url(ar), 302, member=self.area_admin)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        # general approver can confirm
        self.assertGet(self.confirm_url(ar), 302, member=self.approver)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)
        self.assertEqual(ar.assignment.amount, ar.get_amount())
        self.assertEqual(len(mail.outbox), 1)  # confirmation email to user
        self.assertEqual(mail.outbox[0].to[0], self.member.email)

    def test_assignment_confirmation_in_area(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.area_admin))
        # approver for other area can not confirm can not approve
        self.assertGet(self.confirm_url(ar), 302, member=self.member2)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertGet(self.confirm_url(ar), 302, member=self.area_admin)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)

    def test_assignment_confirmation_without_area(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.area_admin, activityarea=None))
        # approver for other area can not confirm can not approve
        self.assertGet(self.confirm_url(ar), 302, member=self.member2)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertGet(self.confirm_url(ar), 302, member=self.approver)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)

    def test_edit_approved_assignment_of_request(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver, approved=True))
        # make sure that amount is restored correctly
        ar.assignment.amount = 20
        ar.save()
        self.assertEqual(ar.assignment.amount, ar.get_amount())

    def test_assignment_confirmation_with_response_by_other_approver(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        self.assertGet(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)), member=self.approver)
        self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                        self.assignment_response_data('confirm'), 302, member=self.approver2)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)
        self.assertEqual(ar.approver, self.approver2)  # approver changed to actual approver
        self.assertEqual(ar.assignment.amount, ar.get_amount())
        self.assertEqual(len(mail.outbox), 2)  # rejection email to user and information to original approver
        self.assertEqual(mail.outbox[0].to[0], self.approver.email)
        self.assertEqual(mail.outbox[1].to[0], self.member.email)

    def assignment_response(self, decision='submit', expected_status=AssignmentRequest.REQUESTED):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        # area approvers can not reply to this.
        self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                        self.assignment_response_data(decision), 302, member=self.member2)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 0)
        self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                        self.assignment_response_data(decision), 302, member=self.area_admin)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 0)
        # only general approver can
        self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                        self.assignment_response_data(decision), 302, member=self.approver)
        ar.refresh_from_db()
        self.assertEqual(ar.status, expected_status)
        self.assertEqual(len(mail.outbox), 1)  # reply email to user
        self.assertEqual(mail.outbox[0].to[0], self.member.email)

    def test_assignment_reply(self):
        self.assignment_response()

    def test_assignment_rejection(self):
        self.assignment_response('reject', AssignmentRequest.REJECTED)

    def test_assignment_response_in_area(self):
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.area_admin))
        # approver for other area can not confirm can not respond
        self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                        self.assignment_response_data('submit'), 302, member=self.member2)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 0)
        self.assertPost(reverse('juntagrico-assignment-request:respond', args=(ar.pk,)),
                        self.assignment_response_data('submit'), 302, member=self.area_admin)
        ar.refresh_from_db()
        self.assertEqual(len(mail.outbox), 1)

    def test_assignment_confirmation_without_key(self):
        # links without (valid) key show the response form instead of confirming
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        for url in (reverse('juntagrico-assignment-request:confirm', args=(ar.pk,)), self.confirm_url(ar, 'wrong'),
                    self.confirm_url(ar, 'ungültig')):
            response = self.assertGet(url, 302, member=self.approver)
            self.assertRedirects(response, reverse('juntagrico-assignment-request:respond', args=(ar.pk,)))
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(len(mail.outbox), 0)

    def test_assignment_confirmation_without_key_for_old_request(self):
        # requests from before the key was introduced have no key and are confirmed with the link from their emails
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        AssignmentRequest.objects.filter(pk=ar.pk).update(confirm_key=None)
        response = self.assertGet(self.confirm_url(ar, 'wrong'), 302, member=self.approver)
        self.assertRedirects(response, reverse('juntagrico-assignment-request:respond', args=(ar.pk,)))
        response = self.assertGet(reverse('juntagrico-assignment-request:confirm', args=(ar.pk,)), 302,
                                  member=self.approver)
        self.assertRedirects(response, reverse('juntagrico-assignment-request:list'))
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)

    def test_assignment_confirmation_old_request_link_after_edit(self):
        # editing an old request generates a key, such that the link without key from its first email is invalid
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        AssignmentRequest.objects.filter(pk=ar.pk).update(confirm_key=None)
        self.assertPost(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)),
                        self.assignment_request_data(self.approver, for_form=True, amount=99), 302)
        response = self.assertGet(reverse('juntagrico-assignment-request:confirm', args=(ar.pk,)), 302,
                                  member=self.approver)
        self.assertRedirects(response, reverse('juntagrico-assignment-request:respond', args=(ar.pk,)))
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)

    def test_assignment_confirmation_link_after_edit(self):
        # link from the first email must not confirm the edited request
        ar = AssignmentRequest.objects.create(**self.assignment_request_data(self.approver))
        old_url = self.confirm_url(ar)
        self.assertPost(reverse('juntagrico-assignment-request:edit', args=(ar.pk,)),
                        self.assignment_request_data(self.approver, for_form=True, amount=99), 302)
        self.client.force_login(self.approver.user)
        response = self.client.get(old_url, follow=True)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.REQUESTED)
        self.assertEqual(response.context['form']['amount'].value(), 99)
        # link from the new email confirms
        self.assertIn(self.confirm_url(ar), mail.outbox[-1].body)
        self.assertGet(self.confirm_url(ar), 302, member=self.approver)
        ar.refresh_from_db()
        self.assertEqual(ar.status, AssignmentRequest.CONFIRMED)

    def test_request_mail_contains_confirm_key(self):
        self.assertPost(reverse('juntagrico-assignment-request:request'),
                        self.assignment_request_data(self.approver, for_form=True), 302)
        ar = AssignmentRequest.objects.get(approver=self.approver)
        self.assertIn(self.confirm_url(ar), mail.outbox[0].body)
