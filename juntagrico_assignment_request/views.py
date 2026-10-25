from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from juntagrico.view_decorators import highlighted_menu

from juntagrico_assignment_request.forms import AssignmentRequestForm, AssignmentResponseForm
from juntagrico_assignment_request.mailer import membernotification, adminnotification
from juntagrico_assignment_request.models import AssignmentRequest
from juntagrico_assignment_request.view_decorators import approver_required, approver_for_request_required


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
    assignment_request_form = AssignmentRequestForm(request.POST or None, member=member)
    if request.method == 'POST' and assignment_request_form.is_valid():
        # Create request
        assignment_request = assignment_request_form.instance
        assignment_request.member = member
        assignment_request.save()
        adminnotification.request_created(assignment_request)
        messages.success(request, mark_safe(text['request_sent']))
        # do a redirect to avoid resending on reloading
        return redirect('juntagrico-assignment-request:request')

    renderdict = {
        'assignment_requests': AssignmentRequest.objects.filter(member=member).pending(),
        'form': assignment_request_form,
        'limit_error': assignment_request_form.new_request_limit_error(),
    }
    return render(request, "assignment_request/request.html", renderdict)


@login_required
@highlighted_menu('request_assignment')
def delete_request_assignment(request, request_id):
    """
    Delete an assignment request.
    GET requests (e.g. links in emails) show a confirmation page.
    """

    assignment_request = get_object_or_404(AssignmentRequest, id=request_id)
    if assignment_request.member != request.user.member or assignment_request.assignment:
        return redirect('juntagrico-assignment-request:request')
    if request.method == 'POST':
        assignment_request.delete()
        return redirect('juntagrico-assignment-request:request')
    return render(request, "assignment_request/delete.html", {'assignment_request': assignment_request})


@login_required
@highlighted_menu('request_assignment')
def edit_request_assignment(request, request_id, text_override=None):
    """
    Edit and assignment request
    """

    text = dict(
        changed=_("Deine Änderungen wurden gespeichert."),
        rerequested=_("Deine Änderungen wurden gespeichert und zur (erneuten) Bestätigung verschickt."),
        confirmed=_("Bestätigte Anfragen können nicht mehr geändert werden.")
    )
    text.update(text_override or {})

    member = request.user.member
    assignment_request = get_object_or_404(AssignmentRequest, id=request_id, member=member)
    if assignment_request.is_confirmed():
        # the confirmed assignment must not be changed without approval
        messages.warning(request, text['confirmed'])
        return redirect('juntagrico-assignment-request:request')
    old_approver = assignment_request.approver
    assignment_request_form = AssignmentRequestForm(request.POST or None, instance=assignment_request, member=member)
    if request.method == 'POST' and assignment_request_form.is_valid():
        # edit request
        new_request = assignment_request_form.instance
        # invalidate confirmation links of previous emails
        new_request.renew_confirm_key()
        if assignment_request_form.amount_increased():
            # if significant changes were made re-approval is needed
            notify = assignment_request_form.sends_notification()
            new_request.status = AssignmentRequest.REQUESTED
            new_request.request_date = date.today()
            new_request.save()
            if notify:
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


@approver_required
def list_assignment_requests(request):
    """
    List assignment requests
    """
    ar = AssignmentRequest.objects.filter(status=AssignmentRequest.REQUESTED).for_approver(request.user.member)
    renderdict = {
        'assignment_requests': ar,
    }
    return render(request, "assignment_request/list.html", renderdict)


@approver_required
def list_archive(request):
    ar = AssignmentRequest.objects.exclude(status=AssignmentRequest.REQUESTED).for_approver(request.user.member)
    renderdict = {
        'assignment_requests': ar,
        'archive': True
    }
    return render(request, "assignment_request/list.html", renderdict)


@approver_for_request_required
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

    areas = None
    if not request.user.has_perm('juntagrico_assignment_request.can_confirm_assignments'):
        # approvers of area can only assign their areas
        areas = request.user.member.coordinated_areas.all()
    assignment_response_form = AssignmentResponseForm(request.POST or None, instance=assignment_request, areas=areas)
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


@approver_for_request_required
def confirm_assignment_request(request, request_id, text_override=None):
    """
    Confirm an assignment request directly with the link from the email.
    Without a valid key, e.g. because the request was changed in the meantime, the response form is shown instead.
    Requests from before the key was introduced are still confirmed with the link without key from their emails
    """
    text = dict(
        confirmed=_("Anfrage bestätigt."),
        already_confirmed=_("Anfrage bereits bestätigt."),
        changed=_("Die Anfrage wurde inzwischen geändert. Bitte prüfe sie, bevor du sie bestätigst.")
    )
    text.update(text_override or {})

    assignment_request = get_object_or_404(AssignmentRequest, id=request_id)
    if assignment_request.is_confirmed():
        messages.warning(request, text['already_confirmed'])
        return redirect('juntagrico-assignment-request:list')
    key = request.GET.get('key')
    if not assignment_request.check_confirm_key(key):
        if key:
            messages.warning(request, text['changed'])
        return redirect('juntagrico-assignment-request:respond', request_id=request_id)

    assignment_request.response_date = date.today()
    assignment_request.response = ''
    assignment_request.status = AssignmentRequest.CONFIRMED
    adminnotification.request_handled_by_other_approver(assignment_request, request.user.member)
    # overwrite approver in any case to actual approver
    assignment_request.approver = request.user.member
    assignment_request.save()
    membernotification.request_handled(assignment_request)
    messages.success(request, text['confirmed'])
    return redirect('juntagrico-assignment-request:list')
