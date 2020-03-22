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
    # path('load-invoices-backup-file/', login_required(views.Invoices2Ftp.as_view()), name='invoices_backup', ),
	# path('send/JPK/', login_required(views.JPK2Accountancy.as_view()), name='send_jpk_files'),
	path('serialize_database/', login_required(views.SerializingView.as_view()), name='serialize_database'),
	path('load-database/', login_required(views.RestoreDataBase.as_view()), name='load-database'),
	path('quiz/', login_required(views.QuizView.as_view()), name='quiz'),
	path('quiz/<uuid:quiz_id>/', login_required(views.QuizView.as_view()), name='quiz'),
    path('exit/', views.exit, name='exit'),
]
