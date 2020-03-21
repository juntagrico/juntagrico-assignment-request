# encoding: utf-8

from django.conf import settings


class AssignmentRequestConfig:
    def __init__(self):
        pass

    @staticmethod
    def emails(key):
        if hasattr(settings, 'EMAILS'):
            if key in settings.EMAILS:
                return settings.EMAILS[key]
        return {
            'new_assignment_request_mail': 'assignment_request/mails/new_assignment_request_mail.txt',
            'edited_assignment_request_mail': 'assignment_request/mails/edited_assignment_request_mail.txt',
            'responded_assignment_request_mail': 'assignment_request/mails/responded_assignment_request_mail.txt',
            'confirmed_assignment_request_mail': 'assignment_request/mails/confirmed_assignment_request_mail.txt',
            'rejected_assignment_request_mail': 'assignment_request/mails/rejected_assignment_request_mail.txt',
            'notify_original_approver_mail': 'assignment_request/mails/notify_original_approver_mail.txt',
        }[key]
