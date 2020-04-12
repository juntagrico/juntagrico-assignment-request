from django.template.loader import get_template

from juntagrico.mailer import EmailSender, base_dict
from juntagrico.config import Config

from juntagrico_assignment_request.mailer import get_approver_emails
from juntagrico_assignment_request.config import AssignmentRequestConfig


def request_created(assignment_request):
    d = base_dict({'assignment_request': assignment_request})
    plaintext = get_template(AssignmentRequestConfig.emails('new_assignment_request_mail'))

    content = plaintext.render(d)
    EmailSender.get_sender(Config.organisation_name() + ' - Neue Böhnli-Anfrage', content)\
        .send_to(get_approver_emails(assignment_request))


def request_handled_by_other_approver(assignment_request, new_approver):
    """
    notify original approver, if another approver handled the request
    """
    if assignment_request.approver and assignment_request.approver != new_approver:
        d = base_dict({
            'assignment_request': assignment_request,
            'new_approver': new_approver
        })
        plaintext = get_template(AssignmentRequestConfig.emails('notify_original_approver_mail'))

        content = plaintext.render(d)
        EmailSender.get_sender(Config.organisation_name()+' - Böhnli-Anfrage erledigt', content)\
            .send_to(get_approver_emails(assignment_request))


def request_changed(assignment_request):
    d = base_dict({'assignment_request': assignment_request})
    plaintext = get_template(AssignmentRequestConfig.emails('edited_assignment_request_mail'))

    content = plaintext.render(d)
    EmailSender.get_sender(Config.organisation_name()+' - Böhnli-Anfrage bearbeitet', content)\
        .send_to(get_approver_emails(assignment_request))
