# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from accountancy import views

# Create your Uniform Resource Locator here.

app_name = 'accountancy'

urlpatterns = [
	path('', login_required(views.AccountancyDocumentView.as_view()), name='accountancy'),
	path('<int:company_id>/', login_required(views.AccountancyDocumentView.as_view()), name='accountancy'),
	path('<int:company_id>/<int:customer_id>/', login_required(views.AccountancyDocumentView.as_view()), name='accountancy'),
	path('<int:company_id>/<int:customer_id>/<int:document_id>/', login_required(views.AccountancyDocumentView.as_view()), name='accountancy'),
	path('add_product/<int:company_id>/<int:customer_id>/<int:document_id>/', login_required(views.AccountancyProductsAddView.as_view()), name='add_product'),
	path('new_product/<int:company_id>/<int:customer_id>/<int:document_id>/', login_required(views.NewProductAddView.as_view()), name='new_product'),
	path('delete_product/<int:record>/<int:company_id>/<int:customer_id>/<int:document_id>/', login_required(views.AccountancyProductDelete.as_view()), name='delete_product'),
    path('add_customer/', login_required(views.CustomerAddView.as_view()), name='add_customer'),
	path('change_customer/<int:customer_id>/', login_required(views.CustomerAddView.as_view()), name='change_customer'),
]
