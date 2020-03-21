from django.contrib import admin

from juntagrico_assignment_request.entity.assignment_request import AssignmentRequest
from juntagrico_assignment_request.admins.assignment_request_admin import *


admin.site.register(AssignmentRequest, AssignmentRequestAdmin)
