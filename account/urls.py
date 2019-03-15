# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from account import views

# Create your Uniform Resource Locator here.

app_name = 'account'

urlpatterns = [
    path('register/', login_required(views.RegisterView.as_view()), name='register'),
    path('admin-site/', views.AdminView.as_view(), name='admin_site'),
    path('load-invoices-backup-file/', login_required(views.Invoices2Ftp.as_view()), name='invoices_backup', ),
	path('send/JPK/', login_required(views.JPK2Accountancy.as_view()), name='send_jpk_files'),
    path('exit/', views.exit, name='exit'),
]
