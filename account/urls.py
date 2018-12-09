# django core
from django.urls import path

# my views
from account import views

app_name = 'account'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('admin-site/', views.AdminView.as_view(), name='admin_site'),
    path('exit/', views.exit, name='exit'),
]
