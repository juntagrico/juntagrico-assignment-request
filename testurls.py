"""
test URL Configuration for calendar development
"""
from django.contrib import admin
import juntagrico
from django.urls import path, include

urlpatterns = [
    path(r'admin/', admin.site.urls),
    path(r'', include('juntagrico.urls')),
    path(r'', include('juntagrico_assignment_request.urls')),
    path(r'', juntagrico.views.home),
]
