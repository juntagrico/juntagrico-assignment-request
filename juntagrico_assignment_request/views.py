from datetime import date

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from juntagrico.view_decorators import highlighted_menu

from juntagrico_assignment_request.dao.assignmentrequestdao import AssignmentRequestDao
from juntagrico_assignment_request.forms import AssignmentRequestForm, AssignmentResponseForm
from juntagrico_assignment_request.mailer import membernotification, adminnotification
from juntagrico_assignment_request.models import AssignmentRequest


@login_required
@highlighted_menu('request_assignment')
def request_assignment(request, sent=False):
    """
    Request an assignment
    """

    member = request.user.member
    assignment_request_form = AssignmentRequestForm(request.POST or None)
    if request.method == 'POST' and assignment_request_form.is_valid():
        # Create request
        assignment_request = assignment_request_form.instance
        assignment_request.member = member
        assignment_request.save()
        adminnotification.request_created(assignment_request)
        return redirect('ar-assignment-requested')

    renderdict = {
        'assignment_requests': AssignmentRequestDao.current_requests_by_member(member),
        'form': assignment_request_form,
        'sent': sent
    }
    return render(request, "assignment_request/request_assignment.html", renderdict)


@login_required
def delete_request_assignment(request, request_id):
    """
    Delete an assignment request
    """

    assignment_request = get_object_or_404(AssignmentRequest, id=request_id)
    if assignment_request.member == request.user.member\
            and not assignment_request.assignment:
        assignment_request.delete()
    return redirect('ar-request-assignment')


@login_required
@highlighted_menu('request_assignment')
def edit_request_assignment(request, request_id):
    """
    Edit and assignment request
    """

    member = request.user.member
    assignment_request = get_object_or_404(AssignmentRequest, id=request_id, member=member)
    assignment_request_form = AssignmentRequestForm(request.POST or None, instance=assignment_request)
    if request.method == 'POST' and assignment_request_form.is_valid():
        # edit request
        assignment_request = assignment_request_form.instance
        assignment_request.status = AssignmentRequest.REQUESTED
        assignment_request.save()
        adminnotification.request_changed(assignment_request)
        return redirect('ar-assignment-requested')

    renderdict = {
        'form': assignment_request_form,
    }
    return render(request, "assignment_request/edit_assignment_request.html", renderdict)


def filter_approver(user):
    if user.has_perm('juntagrico_assignment_request.notified_on_unapproved_assignments'):
        return Q(approver=user.member) | Q(approver__isnull=True)
    return Q(approver=user.member)


@permission_required('juntagrico_assignment_request.can_confirm_assignments')
def list_assignment_requests(request):
    """
    List assignment requests
    """
    ar = AssignmentRequest.objects.filter(status=AssignmentRequest.REQUESTED).filter(filter_approver(request.user))
    renderdict = {
        'assignment_requests': ar,
    }
    return render(request, "assignment_request/list_assignment_requests.html", renderdict)


@permission_required('juntagrico_assignment_request.can_confirm_assignments')
def list_archive(request):
    ar = AssignmentRequest.objects.exclude(status=AssignmentRequest.REQUESTED).filter(filter_approver(request.user))
    renderdict = {
        'assignment_requests': ar,
        'archive': True
    }
    return render(request, "assignment_request/list_assignment_requests.html", renderdict)


@permission_required('juntagrico_assignment_request.can_confirm_assignments')
def respond_assignment_request(request, request_id):
    """
    Confirm or reject an assignment request
    """

    assignment_request = get_object_or_404(AssignmentRequest, id=request_id)
    assignment_response_form = AssignmentResponseForm(request.POST or None, instance=assignment_request)
    if request.method == 'POST' and assignment_response_form.is_valid():
        assignment_request = assignment_response_form.instance
        assignment_request.response_date = date.today()
        if 'confirm' in request.POST:
            assignment_request.status = AssignmentRequest.CONFIRMED
        elif 'reject' in request.POST:
            assignment_request.status = AssignmentRequest.REJECTED
        adminnotification.request_handled_by_other_approver(assignment_request, request.user.member)
        assignment_request.approver = request.user.member
        assignment_request.save()
        membernotification.request_handled(assignment_request)
        return redirect('ar-list-assignment-requests')

    renderdict = {
        'assignment_request': assignment_request,
        'form': assignment_response_form,
    }
    return render(request, "assignment_request/respond_assignment_request.html", renderdict)


@permission_required('juntagrico_assignment_request.can_confirm_assignments')
def confirm_assignment_request(request, request_id):
    """
    Confirm an assignment request directly
    """
    assignment_request = get_object_or_404(AssignmentRequest, id=request_id)
    if not assignment_request.is_confirmed():
        assignment_request.response_date = date.today()
        assignment_request.response = ''
        assignment_request.status = AssignmentRequest.CONFIRMED
        adminnotification.request_handled_by_other_approver(assignment_request, request.user.member)
        # overwrite approver in any case to actual approver
        assignment_request.approver = request.user.member
        assignment_request.save()
        membernotification.request_handled(assignment_request)
    return redirect('ar-list-assignment-requests')
