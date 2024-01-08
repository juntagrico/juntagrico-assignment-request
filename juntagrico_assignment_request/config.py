# encoding: utf-8

from django.conf import settings


class AssignmentRequestConfig:
    @staticmethod
    def emails(key):
        if hasattr(settings, 'EMAILS') and key in settings.EMAILS:
            return settings.EMAILS[key]
        return {
            'new_assignment_request_mail': 'assignment_request/mails/admin/new.txt',
            'edited_assignment_request_mail': 'assignment_request/mails/admin/edited.txt',
            'responded_assignment_request_mail': 'assignment_request/mails/member/responded.txt',
            'confirmed_assignment_request_mail': 'assignment_request/mails/member/confirmed.txt',
            'rejected_assignment_request_mail': 'assignment_request/mails/member/rejected.txt',
            'notify_original_approver_mail': 'assignment_request/mails/admin/notify_original_approver.txt',
        }[key]
