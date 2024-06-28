from functools import wraps

from django.shortcuts import redirect
from juntagrico.view_decorators import any_permission_required

from juntagrico_assignment_request.models import AssignmentRequest

approver_required = any_permission_required('juntagrico_assignment_request.can_confirm_assignments',
                                            'juntagrico_assignment_request.can_confirm_assignments_for_area')


def approver_for_request_required(view):
    @wraps(view)
    def wrapper(request, request_id, *args, **kwargs):
        if request.user.has_perm('juntagrico_assignment_request.can_confirm_assignments'):
            # general approver can approve any request.
            return view(request, request_id, *args, **kwargs)
        elif request.user.has_perm('juntagrico_assignment_request.can_confirm_assignments_for_area'):
            # Note: this is made robust for case that area coordinator changes between request and approval.
            if AssignmentRequest.objects.filter(id=request_id, approver=request.user.member).exists():
                # approver of area can only approve requests to them.
                return view(request, request_id, *args, **kwargs)
            else:
                return redirect('juntagrico-assignment-request:list')
        else:
            # others can't approve
            return redirect('login')
    return wrapper
