from datetime import datetime, time
from django.utils.timezone import get_default_timezone as gdtz

from django.contrib.auth.models import Permission
from django.db.models.query import Q

from juntagrico.models import Member
from juntagrico.util.temporal import start_of_business_year

from juntagrico_assignment_request.entity.assignment_request import AssignmentRequest


class AssignmentRequestDao:

    @staticmethod
    def all_approvers():
        perm = Permission.objects.get(codename='can_confirm_assignments')
        return Member.objects.filter(Q(user__groups__permissions=perm) | Q(user__user_permissions=perm)).distinct()

    @staticmethod
    def all_notified_on_unapproved_assignments():
        perm = Permission.objects.get(codename='notified_on_unapproved_assignments')
        return Member.objects.filter(Q(user__groups__permissions=perm) | Q(user__user_permissions=perm)).distinct()

    @staticmethod
    def current_requests_by_member(member):
        start = gdtz().localize(datetime.combine(start_of_business_year(), time.min))
        return AssignmentRequest.objects.filter(member=member).\
            filter(Q(status=AssignmentRequest.REQUESTED) | Q(job_time__gte=start))
