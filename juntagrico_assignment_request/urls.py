"""juntagrico_crowdfunding URL Configuration
"""
from django.urls import path
from juntagrico_assignment_request import views

app_name = 'juntagrico-assignment-request'
urlpatterns = [
    path('ar/assignment/request', views.request_assignment, name='request'),
    path('ar/assignment/delete/<int:request_id>/', views.delete_request_assignment, name='delete'),
    path('ar/assignment/edit/<int:request_id>/', views.edit_request_assignment, name='edit'),
    path('ar/assignment/list', views.list_assignment_requests, name='list'),
    path('ar/assignment/archive', views.list_archive, name='archive'),
    path('ar/assignment/respond/<int:request_id>/', views.respond_assignment_request, name='respond'),
    path('ar/assignment/confirm/<int:request_id>/', views.confirm_assignment_request, name='confirm'),
]
