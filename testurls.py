"""
test URL Configuration for calendar development
"""
from django.conf.urls import include, url
from django.contrib import admin
import juntagrico

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('juntagrico.urls')),
    url(r'^', include('calendar.urls')),
    url(r'^$', juntagrico.views.home),
]
