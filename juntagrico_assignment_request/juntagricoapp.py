from juntagrico.admins.job_admin import JobAdmin
from juntagrico.admins.job_type_admin import JobTypeAdmin
from juntagrico.util import addons

import juntagrico_assignment_request

addons.config.register_user_menu('assignment_request/menu/assignment_request_user_menu.html')
addons.config.register_admin_menu('assignment_request/menu/assignment_request_admin_menu.html')
addons.config.register_version(juntagrico_assignment_request.name, juntagrico_assignment_request.version)


#############################################
# Hide automatically generated jobs and types
# in admin by monkey patching

def get_job_type_queryset(self, request):
    return original_get_job_type_queryset(self, request).filter(
        recuringjob__assignment__assignmentrequest__isnull=True).distinct()


def get_job_queryset(self, request):
    return original_get_job_queryset(self, request).filter(
        assignment__assignmentrequest__isnull=True).distinct()


original_get_job_type_queryset = JobTypeAdmin.get_queryset
JobTypeAdmin.get_queryset = get_job_type_queryset
original_get_job_queryset = JobAdmin.get_queryset
JobAdmin.get_queryset = get_job_queryset
