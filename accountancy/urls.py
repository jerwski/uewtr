# django core
from django.urls import path
from django.contrib.auth.decorators import login_required

# my views
from accountancy import views

# Create your Uniform Resource Locator here.

app_name = 'accountancy'

urlpatterns = [
	path('', login_required(views.AccountancyDocumentView.as_view()), name='accountancy'),
	path('company=<int:company_id>/', login_required(views.AccountancyDocumentView.as_view()), name='accountancy'),
	path('company=<int:company_id>/customer=<int:customer_id>/', login_required(views.AccountancyDocumentView.as_view()), name='accountancy'),
	path('company=<int:company_id>/customer=<int:customer_id>/doc_id=<int:document_id>/', login_required(views.AccountancyDocumentView.as_view()), name='accountancy'),
	path('edit_product/company=<int:company_id>/customer=<int:customer_id>/doc_id=<int:document_id>/product=<int:product_id>/', login_required(views.AccountancyProductsAddView.as_view()), name='edit_product'),
	path('add_product/company=<int:company_id>/customer=<int:customer_id>/doc_id=<int:document_id>/', login_required(views.AccountancyProductsAddView.as_view()), name='add_product'),
	path('add_product/company=<int:company_id>/customer=<int:customer_id>/doc_id=<int:document_id>/product=<int:new_id>/', login_required(views.AccountancyProductsAddView.as_view()), name='add_product'),
	path('new_product/company=<int:company_id>/customer=<int:customer_id>/doc_id=<int:document_id>/', login_required(views.NewProductAddView.as_view()), name='new_product'),
	path('delete_product/record=<int:record>/company=<int:company_id>/customer=<int:customer_id>/doc_id<int:document_id>/', login_required(views.AccountancyProductDelete.as_view()), name='delete_product'),
    path('add_customer/', login_required(views.CustomerAddView.as_view()), name='add_customer'),
	path('change_customer/customer=<int:customer_id>/', login_required(views.CustomerAddView.as_view()), name='change_customer'),
]
