from django.contrib.auth.models import Permission
from django.db.models import Q
from juntagrico.entity.member import Member


def get_approvers(general_only=False):
    codenames = ['can_confirm_assignments']
    if not general_only:
        codenames.append('can_confirm_assignments_for_area')
    perms = Permission.objects.filter(codename__in=codenames)
    return Member.objects.filter(
        Q(user__groups__permissions__in=perms) | Q(user__user_permissions__in=perms)
    ).distinct()


def all_notified_on_unapproved_assignments():
    perm = Permission.objects.get(codename='notified_on_unapproved_assignments')
    return Member.objects.filter(Q(user__groups__permissions=perm) | Q(user__user_permissions=perm)).distinct()
