# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from cashregister import views

app_name = 'cashregister'

urlpatterns = [
    path('add_company/', login_required(views.CompanyAddView.as_view()), name='add_company'),
    path('change_company/<int:company_id>/', login_required(views.CompanyAddView.as_view()), name='change_company'),
]