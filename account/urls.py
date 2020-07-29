# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from account import views

# Create your Uniform Resource Locator here.

app_name = 'account'

urlpatterns = [
    path('register/', login_required(views.RegisterView.as_view()), name='register'),
    path('dashboard/', views.AdminView.as_view(), name='dashboard'),
	path('serialize/', login_required(views.SerializeView.as_view()), name='serialize_database'),
	path('deserialize/', login_required(views.DeserializeView.as_view()), name='deserialize_database'),
	path('load-database/', login_required(views.RestoreDataBase.as_view()), name='load-database'),
	path('quiz/', login_required(views.QuizView.as_view()), name='quiz'),
	path('quiz/<uuid:quiz_id>/', login_required(views.QuizView.as_view()), name='quiz'),
    path('exit/', views.exit, name='exit'),
]
