from django.contrib.auth.models import Permission
from django.db.models import Q
from juntagrico.entity.member import Member


def all_approvers():
    perm = Permission.objects.get(codename='can_confirm_assignments')
    return Member.objects.filter(Q(user__groups__permissions=perm) | Q(user__user_permissions=perm)).distinct()


def all_notified_on_unapproved_assignments():
    perm = Permission.objects.get(codename='notified_on_unapproved_assignments')
    return Member.objects.filter(Q(user__groups__permissions=perm) | Q(user__user_permissions=perm)).distinct()