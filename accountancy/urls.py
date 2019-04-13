# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from accountancy import views

# Create your Uniform Resource Locator here.

app_name = 'accountancy'

urlpatterns = [
    path('add_customer/', login_required(views.CustomerAddView.as_view()), name='add_customer'),
	path('change_customer/<int:customer_id>/', login_required(views.CustomerAddView.as_view()), name='change_customer'),
]
