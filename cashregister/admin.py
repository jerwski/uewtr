# django library
from django.contrib import admin

# my models
from cashregister.models import Company, CashRegister

# my functions
from functions.archive import export_as_json

# Register your models here.


export_as_json.short_description = 'Export selected records to json file'


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company', 'nip', 'street', 'city', 'postal', 'phone', 'account', 'status', 'created', 'updated')
    list_filter = ('company', 'created')
    ordering = ['company']
    actions = [export_as_json]


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ('company', 'date', 'symbol', 'contents', 'income', 'expenditure')
    list_filter = ('company', 'date')
    ordering = ['company', '-date']
    actions = [export_as_json]
