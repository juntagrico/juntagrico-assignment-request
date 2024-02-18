from django.template.loader import get_template

from juntagrico.mailer import EmailSender, base_dict
from juntagrico.config import Config

from juntagrico_assignment_request.mailer import get_approver_emails


def content_render(assignment_request, template, **kwargs):
    kwargs.update({'assignment_request': assignment_request})
    d = base_dict(kwargs)
    plaintext = get_template('assignment_request/mails/admin/' + template + '.txt')
    return plaintext.render(d)


def request_created(assignment_request):
    EmailSender.get_sender(Config.organisation_name() + ' - Neue ' + Config.vocabulary('assignment') + '-Anfrage',
                           content_render(assignment_request, 'new'))\
        .send_to(get_approver_emails(assignment_request))


def request_handled_by_other_approver(assignment_request, new_approver):
    """
    notify original approver, if another approver handled the request
    """
    if assignment_request.approver and assignment_request.approver != new_approver:
        EmailSender.get_sender(Config.organisation_name() + ' - ' + Config.vocabulary('assignment') + '-Anfrage erledigt',
                               content_render(assignment_request, 'notify_original_approver',
                                              new_approver=new_approver))\
            .send_to(get_approver_emails(assignment_request))


def request_changed(assignment_request):
    EmailSender.get_sender(Config.organisation_name() + ' - ' + Config.vocabulary('assignment') + '-Anfrage bearbeitet',
                           content_render(assignment_request, 'edited'))\
        .send_to(get_approver_emails(assignment_request))
