from django.utils.translation import gettext as _
from django.template.loader import get_template

from juntagrico.mailer import EmailSender, base_dict
from juntagrico.config import Config


def request_handled(assignment_request):
    d = base_dict({'assignment_request': assignment_request})

    if assignment_request.is_confirmed():
        subject = _('{} bestätigt').format(Config.vocabulary('assignment'))
        content = get_template('assignment_request/mails/member/confirmed.txt').render(d)
    elif assignment_request.is_rejected():
        subject = _('{} nicht bestätigt').format(Config.vocabulary('assignment'))
        content = get_template('assignment_request/mails/member/rejected.txt').render(d)
    else:
        subject = _('Rückfrage zu deinem/r {}').format(Config.vocabulary('assignment'))
        content = get_template('assignment_request/mails/member/responded.txt').render(d)

    EmailSender.get_sender(Config.organisation_name() + ' - ' + subject, content,
                           reply_to=[assignment_request.approver.email]).send_to(assignment_request.member.email)
