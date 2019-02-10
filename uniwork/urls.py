"""uniwtr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# django core
from django.contrib import admin
from django.contrib.auth import urls
from django.urls import path, include
from django.views.generic import RedirectView

# my apps
from account import views


urlpatterns = [
    path('', include(urls)),
    path('admin/doc/', include('django.contrib.admindocs.urls')), # must to be before path admin/
    path('admin/', admin.site.urls),
    path('', views.AdminView.as_view()),
    path('account/', include('account.urls', namespace='account')),
    path('employee/', include('employee.urls', namespace='employee')),
    path('evidence/', include('evidence.urls', namespace='evidence')),
    path(r'favicon/.ico', RedirectView.as_view(url='/static/images/favicon.ico')),
    path('search/', include('haystack.urls')),
]

admin.site.site_title = '/admin/'
admin.site.site_header = 'Employee Working Time Recorder'
admin.site.index_title = 'Uniwork administration'
