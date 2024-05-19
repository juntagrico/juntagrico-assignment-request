from django.contrib.auth.models import Permission
from django.db.models import Q
from juntagrico.entity.member import Member


def get_approvers(general_only=False):
    general = Permission.objects.get(codename='can_confirm_assignments')
    area = Permission.objects.get(codename='can_confirm_assignments_for_area')
    query = Q(user__groups__permissions=general) | Q(user__user_permissions=general)
    if not general_only:
        query |= (Q(user__groups__permissions=area) | Q(user__user_permissions=area)) & Q(activityarea__isnull=False)
    return Member.objects.filter(query).distinct()


def all_notified_on_unapproved_assignments():
    perm = Permission.objects.get(codename='notified_on_unapproved_assignments')
    return Member.objects.filter(Q(user__groups__permissions=perm) | Q(user__user_permissions=perm)).distinct()
