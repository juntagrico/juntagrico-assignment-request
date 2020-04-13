from django.contrib.auth.models import Permission
from django.test import override_settings, TestCase
from django.utils import timezone
from juntagrico.entity.jobs import ActivityArea
from juntagrico.entity.member import Member

from juntagrico_assignment_request.entity.assignment_request import AssignmentRequest


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AssignmentRequestTestCase(TestCase):
    def setUp(self):
        self.set_up_member()
        self.set_up_area()

    def assertGet(self, url, code=200, member=None):
        login_member = member or self.member
        self.client.force_login(login_member.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, code)

    def assertPost(self, url, data=None, code=200, member=None):
        login_member = member or self.member
        self.client.force_login(login_member.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, code)

    @staticmethod
    def create_member(email):
        member_data = {'first_name': 'first_name',
                       'last_name': 'last_name',
                       'email': email,
                       'addr_street': 'addr_street',
                       'addr_zipcode': 'addr_zipcode',
                       'addr_location': 'addr_location',
                       'phone': 'phone',
                       'confirmed': True,
                       }
        member = Member.objects.create(**member_data)
        member.user.set_password('12345')
        member.user.save()
        return member

    def set_up_member(self):
        """
        member
        """
        self.member = self.create_member('member@email.org')
        self.approver = self.create_member('approver@email.org')
        self.approver2 = self.create_member('approver2@email.org')
        self.approver.user.user_permissions.add(
            Permission.objects.get(codename='can_confirm_assignments'))
        self.approver.user.save()
        self.approver2.user.user_permissions.add(
            Permission.objects.get(codename='can_confirm_assignments'))
        self.approver2.user.user_permissions.add(
            Permission.objects.get(codename='notified_on_unapproved_assignments'))
        self.approver2.user.save()

    @staticmethod
    def admin():
        """
        admin member
        """
        admin_data = {'first_name': 'admin',
                      'last_name': 'last_name',
                      'email': 'admin@email.org',
                      'addr_street': 'addr_street',
                      'addr_zipcode': 'addr_zipcode',
                      'addr_location': 'addr_location',
                      'phone': 'phone',
                      'confirmed': True,
                      }
        admin = Member.objects.create(**admin_data)
        admin.user.set_password("123456")
        admin.user.is_staff = True
        admin.user.is_superuser = True
        admin.user.save()
        return admin

    def set_up_area(self):
        """
        area
        """
        area_data = {'name': 'name',
                     'coordinator': self.approver}
        area_data2 = {'name': 'name2',
                      'coordinator': self.approver2,
                      'hidden': True}
        self.area = ActivityArea.objects.create(**area_data)
        self.area2 = ActivityArea.objects.create(**area_data2)

    def assignment_request_data(self, approver=None, for_form=False, approved=False):
        if for_form:
            if approver is None:
                approver = ''
            else:
                approver = approver.pk
        date = timezone.now()
        data = {
            'job_time': date.strftime('%Y-%m-%d %H:%M') if for_form else date,
            'duration': 4,
            'amount': 1,
            'approver': approver,
            'activityarea': self.area.pk if for_form else self.area,
            'location': 'location',
            'description': 'description'
        }
        if not for_form:
            data['member'] = self.member
            if approved:
                data['status'] = AssignmentRequest.CONFIRMED
        return data

    def assignment_response_data(self, decision='submit'):
        """
        :param decision: ['confirm', 'reject', 'submit'(default)]
        """
        return {
            'response': 'response',
            decision: True,
            'amount': 2,
            'activityarea': self.area.pk,
            'location': 'location'
        }
