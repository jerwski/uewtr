# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from cashregister import views

# Create your Uniform Resource Locator here.

app_name = 'cashregister'

urlpatterns = [
    path('add_company/', login_required(views.CompanyAddView.as_view()), name='add_company'),
    path('register/', login_required(views.CashRegisterView.as_view()), name='cash_register'),
    path('register/company=<int:company_id>/', login_required(views.CashRegisterView.as_view()), name='cash_register'),
    path('email/pdf/company=<int:company_id>/', login_required(views.CashRegisterSendView.as_view()), name='send_register'),
    path('change_company/company=<int:company_id>/', login_required(views.CompanyAddView.as_view()), name='change_company'),
    path('register/cashaccept/company=<int:company_id>/record=<int:record>/', login_required(views.CashRegisterAcceptView.as_view()), name='cash_accept'),
    path('register/print/company=<int:company_id>/', login_required(views.CashRegisterPrintView.as_view()), name='print_register'),
	path('record/delete/company=<int:company_id>/record=<int:record>/', login_required(views.CashRegisterDelete.as_view()), name='cash_register_delete')
]
