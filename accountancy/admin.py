# django library
from django.contrib import admin

# my models
from accountancy.models import Customer, Product, AccountancyDocument, AccountancyProducts

# my functions
from functions.archive import export_as_json


# Register your models here.


export_as_json.short_description = 'Export selected records to json file'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = ('customer', 'nip', 'street', 'city', 'postal', 'phone', 'email', 'status')
	list_filter = ('customer',)
	ordering = ['customer']
	
	actions = [export_as_json]
	

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'unit', 'netto', 'vat')

	actions = [export_as_json]
	
	
class AccountancyProductsAdminInline(admin.StackedInline):
	model = AccountancyProducts
	extra = 0


@admin.register(AccountancyDocument)
class AccountancyDocumentAdmin(admin.ModelAdmin):
	list_display = ('company', 'customer', 'number', 'conveyance', 'waybill', 'date_of_shipment', 'invoice', 'order')
	list_filter = ('number',)
	ordering = ['number']
	inlines = [AccountancyProductsAdminInline]
	
	actions = [export_as_json]
	