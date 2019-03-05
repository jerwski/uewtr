# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from cashregister import views

app_name = 'cashregister'

urlpatterns = [
    path('add_company/', login_required(views.CompanyAddView.as_view()), name='add_company'),
    path('register/', login_required(views.CashRegisterView.as_view()), name='cash_register'),
    path('register/<int:company_id>/', login_required(views.CashRegisterView.as_view()), name='cash_register'),
    path('email/pdf/<int:company_id>/', login_required(views.CashRegisterSendView.as_view()), name='send_register'),
    path('change_company/<int:company_id>/', login_required(views.CompanyAddView.as_view()), name='change_company'),
    path('register/cashaccept/<int:record>/', login_required(views.CashRegisterAcceptView.as_view()), name='cash_accept'),
    path('register/print/<int:company_id>/', login_required(views.CashRegisterPrintView.as_view()), name='print_register'),
]
