from juntagrico.config import Config

from juntagrico_assignment_request.utils import all_notified_on_unapproved_assignments

'''
Server generated Emails
'''


def get_approver_emails(assignment_request):
    receivers = []
    if assignment_request.approver:
        # Notify approver if defined
        receivers.append(assignment_request.approver.email)
    else:
        # Otherwise inform all that should be notified on unapproved assignments
        for notified in all_notified_on_unapproved_assignments():
            receivers.append(notified.email)
    if not receivers:
        # Nobody? Send it to the info mail then
        receivers.append(Config.info_email())
    return receivers
