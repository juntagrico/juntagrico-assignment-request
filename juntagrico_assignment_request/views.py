from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext as _

from juntagrico.view_decorators import highlighted_menu

from juntagrico_assignment_request.forms import AssignmentRequestForm, AssignmentResponseForm
from juntagrico_assignment_request.mailer import membernotification, adminnotification
from juntagrico_assignment_request.models import AssignmentRequest


@login_required
@highlighted_menu('request_assignment')
def request_assignment(request, text_override=None):
    """
    Request an assignment
    """

    text = dict(
        request_sent=_("Deine Anfrage wurde erfolgreich verschickt.<br>"
                       "Du wirst per E-Mail benachrichtigt, sobald diese bestätigt wurde.")
    )
    text.update(text_override or {})

    member = request.user.member
    assignment_request_form = AssignmentRequestForm(request.POST or None)
    if request.method == 'POST' and assignment_request_form.is_valid():
        # Create request
        assignment_request = assignment_request_form.instance
        assignment_request.member = member
        assignment_request.save()
        adminnotification.request_created(assignment_request)
        messages.success(request, text['request_sent'])
        # do a redirect to avoid resending on reloading
        return redirect('juntagrico-assignment-request:request')

    renderdict = {
        'assignment_requests': AssignmentRequest.objects.filter(member=member).pending(),
        'form': assignment_request_form,
    }
    return render(request, "assignment_request/request.html", renderdict)


@login_required
def delete_request_assignment(request, request_id):
    """
    Delete an assignment request
    """

    assignment_request = get_object_or_404(AssignmentRequest, id=request_id)
    if assignment_request.member == request.user.member\
            and not assignment_request.assignment:
        assignment_request.delete()
    return redirect('juntagrico-assignment-request:request')


@login_required
@highlighted_menu('request_assignment')
def edit_request_assignment(request, request_id, text_override=None):
    """
    Edit and assignment request
    """

    text = dict(
        changed=_("Deine Änderungen wurden gespeichert."),
        rerequested=_("Deine Änderungen wurden gespeichert und zur (erneuten) Bestätigung verschickt.")
    )
    text.update(text_override or {})

    member = request.user.member
    assignment_request = get_object_or_404(AssignmentRequest, id=request_id, member=member)
    old_amount = assignment_request.get_amount()
    old_approver = assignment_request.approver
    assignment_request_form = AssignmentRequestForm(request.POST or None, instance=assignment_request)
    if request.method == 'POST' and assignment_request_form.is_valid():
        # edit request
        new_request = assignment_request_form.instance
        if new_request.get_amount() > old_amount:
            # if significant changes were made re-approval is needed
            new_request.status = AssignmentRequest.REQUESTED
            new_request.save()
            adminnotification.request_changed(new_request)
            messages.success(request, text['rerequested'])
        else:
            if new_request.status is not AssignmentRequest.REQUESTED:
                # keep approver, if they replied already
                new_request.approver = old_approver
            new_request.save()
            messages.success(request, text['changed'])
        return redirect('juntagrico-assignment-request:request')

    renderdict = {
        'form': assignment_request_form,
    }
    return render(request, "assignment_request/edit.html", renderdict)


@permission_required('juntagrico_assignment_request.can_confirm_assignments')
def list_assignment_requests(request):
    """
    List assignment requests
    """
    ar = AssignmentRequest.objects.filter(status=AssignmentRequest.REQUESTED).for_approver(request.user.member)
    renderdict = {
        'assignment_requests': ar,
    }
    return render(request, "assignment_request/list.html", renderdict)


@permission_required('juntagrico_assignment_request.can_confirm_assignments')
def list_archive(request):
    ar = AssignmentRequest.objects.exclude(status=AssignmentRequest.REQUESTED).for_approver(request.user.member)
    renderdict = {
        'assignment_requests': ar,
        'archive': True
    }
    return render(request, "assignment_request/list.html", renderdict)


@permission_required('juntagrico_assignment_request.can_confirm_assignments')
def respond_assignment_request(request, request_id, text_override=None):
    """
    Confirm or reject an assignment request
    """

    text = dict(
        replied=_("Antwort gesendet."),
        already_replied=_("Die Anfrage wurde bereits beantwortet.")
    )
    text.update(text_override or {})

    assignment_request = get_object_or_404(AssignmentRequest, id=request_id)
    if assignment_request.status != AssignmentRequest.REQUESTED:
        messages.warning(request, text['already_replied'])
        return redirect('juntagrico-assignment-request:list')

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
        messages.success(request, text['replied'])
        return redirect('juntagrico-assignment-request:list')

    renderdict = {
        'assignment_request': assignment_request,
        'form': assignment_response_form,
    }
    return render(request, "assignment_request/respond.html", renderdict)


@permission_required('juntagrico_assignment_request.can_confirm_assignments')
def confirm_assignment_request(request, request_id, text_override=None):
    """
    Confirm an assignment request directly
    """
    text = dict(
        confirmed=_("Anfrage bestätigt."),
        already_confirmed=_("Anfrage bereits bestätigt.")
    )
    text.update(text_override or {})

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
        messages.success(request, text['confirmed'])
    else:
        messages.warning(request, text['already_confirmed'])
    return redirect('juntagrico-assignment-request:list')
