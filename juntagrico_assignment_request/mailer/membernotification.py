from django.utils.translation import gettext as _
from django.template.loader import get_template

from juntagrico.mailer import EmailSender, base_dict
from juntagrico.config import Config

from juntagrico_assignment_request.config import AssignmentRequestConfig


def request_handled(assignment_request):
    d = base_dict({'assignment_request': assignment_request})

    if assignment_request.is_confirmed():
        subject = _('{} bestätigt').format(Config.vocabulary('assignment'))
        content = get_template(AssignmentRequestConfig.emails('confirmed_assignment_request_mail')).render(d)
    elif assignment_request.is_rejected():
        subject = _('{} nicht bestätigt').format(Config.vocabulary('assignment'))
        content = get_template(AssignmentRequestConfig.emails('rejected_assignment_request_mail')).render(d)
    else:
        subject = _('Rückfrage zu deinem/r {}').format(Config.vocabulary('assignment'))
        content = get_template(AssignmentRequestConfig.emails('responded_assignment_request_mail')).render(d)

    EmailSender.get_sender(Config.organisation_name() + ' - ' + subject, content,
                           reply_to=[assignment_request.approver.email]).send_to(assignment_request.member.email)
