from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from juntagrico.view_decorators import any_permission_required

from juntagrico_assignment_request.models import AssignmentRequest

approver_required = any_permission_required('juntagrico_assignment_request.can_confirm_assignments',
                                            'juntagrico_assignment_request.can_confirm_assignments_for_area')


def approver_for_request_required(view):
    @wraps(view)
    def wrapper(request, request_id, *args, **kwargs):
        if not request.user.has_perm('juntagrico_assignment_request.can_confirm_assignments') and \
                not request.user.has_perm('juntagrico_assignment_request.can_confirm_assignments_for_area'):
            # others can't approve
            return redirect('login')
        if AssignmentRequest.objects.filter(id=request_id, member=request.user.member).exists():
            # nobody can approve their own requests
            messages.error(request, _('Du kannst deine eigene Anfrage nicht beantworten.'))
            return redirect('juntagrico-assignment-request:list')
        if request.user.has_perm('juntagrico_assignment_request.can_confirm_assignments') or \
                AssignmentRequest.objects.filter(id=request_id, approver=request.user.member).exists():
            # general approver can approve any request, area approver only requests to them.
            # Note: this is made robust for case that area coordinator changes between request and approval.
            return view(request, request_id, *args, **kwargs)
        return redirect('juntagrico-assignment-request:list')
    return wrapper
