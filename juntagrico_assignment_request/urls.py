"""juntagrico_crowdfunding URL Configuration
"""
from django.urls import path
from juntagrico_assignment_request import views as assignment_request

urlpatterns = [
    path('ar/assignment/request', assignment_request.request_assignment, name='ar-request-assignment'),
    path('ar/assignment/requested', assignment_request.request_assignment,
         {'sent': True}, name='ar-assignment-requested'),
    path('ar/assignment/delete/<int:request_id>/', assignment_request.delete_request_assignment,
         name='ar-delete-assignment-request'),
    path('ar/assignment/edit/<int:request_id>/', assignment_request.edit_request_assignment,
         name='ar-edit-assignment-request'),
    path('ar/assignment/list', assignment_request.list_assignment_requests,
         name='ar-list-assignment-requests'),
    path('ar/assignment/archive', assignment_request.list_archive, name='ar-list-archive'),
    path('ar/assignment/respond/<int:request_id>/', assignment_request.respond_assignment_request,
         name='ar-respond-assignment-request'),
    path('ar/assignment/confirm/<int:request_id>/', assignment_request.confirm_assignment_request,
         name='ar-confirm-assignment-request'),
]
